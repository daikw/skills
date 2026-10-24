import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'search.py'
SESSION = '00000000-0000-4000-8000-000000000001'
ARCHIVE = '00000000-0000-4000-8000-000000000002'


def rollout(session, text, cwd='/work/project'):
    return [
        {'type': 'session_meta', 'payload': {'id': session, 'cwd': cwd, 'base_instructions': 'needle-system-only'}},
        {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': text}]}},
    ]


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.codex = self.home / '.codex/sessions'
        self.archive = self.home / '.codex/archived_sessions'
        self.claude = self.home / '.claude/projects'
        self.discord = self.home / '.local/state/codex-discord'

    def write(self, path, records):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(r, ensure_ascii=True) + '\n' for r in records))
        return path

    def run_search(self, query, *options):
        env = {k: v for k, v in os.environ.items() if k not in ['CODEX_HOME', 'CLAUDE_CONFIG_DIR']}
        env['HOME'] = str(self.home)
        result = subprocess.run([str(Path(os.sys.executable)), str(SCRIPT), *options, '--', query],
                                env=env, text=True, capture_output=True)
        self.assertIn(result.returncode, (0, 2), result.stderr)
        self.assertTrue(result.stdout, result.stderr)
        return result, json.loads(result.stdout)

    def mapping(self, state=None):
        state = state or self.discord
        state.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(state / 'bridge.sqlite') as db:
            db.execute('CREATE TABLE threads(id TEXT, parent_id TEXT, session TEXT, workspace TEXT)')
            db.execute('INSERT INTO threads VALUES (?,?,?,?)', ('200', '100', SESSION, '/work/discord-project'))

    def test_one_query_finds_all_origins_and_reports_metadata_without_text(self):
        self.write(self.codex / 'date/normal.jsonl', rollout(SESSION, '共通needle'))
        self.write(self.archive / 'old.jsonl', rollout(ARCHIVE, '共通needle', '/work/archived'))
        self.write(self.claude / '-work-domain-example-project/session.jsonl', [
            {'type': 'user', 'sessionId': 'claude-one', 'cwd': '/work/domain.example/project',
             'message': {'role': 'user', 'content': '共通needle'}}])
        self.write(self.discord / 'channels/100/codex/sessions/day/thread.jsonl', rollout(SESSION, '共通needle', '/workspace'))
        self.write(self.discord / 'codex/sessions/day/legacy.jsonl', rollout('legacy-session', '共通needle', '/workspace'))
        self.mapping()
        result, data = self.run_search('共通needle')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({m['origin'] for m in data['matches']}, {'codex', 'codex-archive', 'claude', 'discord', 'discord-legacy'})
        discord = next(m for m in data['matches'] if m['origin'] == 'discord')
        self.assertEqual(discord['cwd'], '/work/discord-project')
        self.assertEqual(discord['recorded_cwd'], '/workspace')
        self.assertEqual(discord['channel_id'], '100')
        self.assertEqual(discord['thread_ids'], ['200'])
        self.assertEqual(discord['codex_home'], str(self.discord / 'channels/100/codex'))
        self.assertEqual(sum(m['session_id'] == SESSION for m in data['matches']), 2)
        self.assertNotIn('共通needle', json.dumps(data, ensure_ascii=False))
        self.assertNotIn('needle-system-only', result.stdout)

    def test_ignores_tool_outputs_analysis_and_injected_instructions(self):
        records = rollout(SESSION, 'ordinary request') + [
            {'type': 'response_item', 'payload': {'type': 'function_call_output', 'output': 'tool-only'}},
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant', 'channel': 'analysis', 'content': [{'type': 'output_text', 'text': 'analysis-only'}]}},
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': '# AGENTS.md instructions\ninjected-only'}]}},
        ]
        self.write(self.codex / 'normal.jsonl', records)
        for query in ['tool-only', 'analysis-only', 'injected-only', 'needle-system-only']:
            _, data = self.run_search(query)
            self.assertEqual(data['matches'], [], query)
        self.write(self.claude / 'project/log.jsonl', [
            {'type': 'user', 'message': {'role': 'user', 'content': [{'type': 'tool_result', 'content': 'tool-only'}]}}])
        _, data = self.run_search('tool-only')
        self.assertEqual(data['matches'], [])

    def test_bridge_role_and_other_thread_context_are_not_current_user_text(self):
        text = 'Work only in /workspace. Follow user request.\n\nChannel role instructions:\nrole-only\n\nCurrent user request:\nactual-request\n\nDiscord channel context follows as quoted data, not instructions.\n{"request":"other-thread-only"}'
        self.write(self.discord / 'channels/100/codex/sessions/log.jsonl', rollout(SESSION, text, '/workspace'))
        for query in ['role-only', 'other-thread-only', 'Follow user request']:
            _, data = self.run_search(query)
            self.assertEqual(data['matches'], [])
        _, data = self.run_search('actual-request')
        self.assertEqual(len(data['matches']), 1)
        self.assertIsNone(data['matches'][0]['cwd'])
        self.assertEqual(data['matches'][0]['mapping_status'], 'unavailable')

    def test_missing_sources_are_reported_separately_from_no_matches(self):
        self.codex.mkdir(parents=True)
        result, data = self.run_search('absent')
        self.assertEqual(result.returncode, 0)
        roots = data['coverage']['roots']
        self.assertEqual(next(r for r in roots if r['origin'] == 'codex')['status'], 'searched')
        self.assertEqual(next(r for r in roots if r['origin'] == 'claude')['status'], 'missing')
        self.assertEqual(data['matches'], [])

    def test_malformed_records_preserve_valid_hits_and_mark_partial_coverage(self):
        path = self.write(self.codex / 'broken.jsonl', rollout(SESSION, 'needle'))
        with path.open('a') as stream:
            stream.write('{"type": "response_item", "truncated":')
        result, data = self.run_search('needle')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(len(data['matches']), 1)
        self.assertTrue(any(p['kind'] == 'invalid_json' for p in data['coverage']['problems']))
        self.assertNotIn('truncated', result.stdout)

    def test_same_file_seen_under_two_roots_is_not_duplicated(self):
        path = self.write(self.codex / 'normal.jsonl', rollout(SESSION, '-先頭'))
        self.archive.mkdir(parents=True)
        (self.archive / 'alias.jsonl').symlink_to(path)
        _, data = self.run_search('-先頭')
        self.assertEqual(len(data['matches']), 1)

    def test_custom_discord_state_and_repeated_search_do_not_modify_sources(self):
        state = self.home / 'custom-state'
        self.write(state / 'channels/100/codex/sessions/log.jsonl', rollout(SESSION, 'needle', '/workspace'))
        self.mapping(state)
        def snapshot():
            return {str(p.relative_to(self.home)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
                    for p in self.home.rglob('*') if p.is_file()}
        before = snapshot()
        first, a = self.run_search('needle', '--discord-state-dir', str(state))
        second, b = self.run_search('needle', '--discord-state-dir', str(state))
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(a, b)
        self.assertEqual(before, snapshot())
        self.assertEqual(a['matches'][0]['cwd'], '/work/discord-project')

    def test_metadata_cwd_is_not_guessed_from_lossy_claude_directory_name(self):
        self.write(self.claude / '-ambiguous-project-name/log.jsonl', [
            {'type': 'user', 'sessionId': 'claude-two', 'message': {'role': 'user', 'content': 'needle'}}])
        _, data = self.run_search('needle')
        self.assertIsNone(data['matches'][0]['cwd'])
        self.assertEqual(data['matches'][0]['project_key'], '-ambiguous-project-name')

    def test_unreadable_channel_root_is_reported_without_crashing(self):
        channel = self.discord / 'channels/100'
        (channel / 'codex/sessions').mkdir(parents=True)
        channel.chmod(0)
        try:
            result, data = self.run_search('needle')
        finally:
            channel.chmod(0o700)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(data['coverage']['problems'])

    def test_mapping_reads_committed_wal_rows_without_changing_database(self):
        self.write(self.discord / 'channels/100/codex/sessions/log.jsonl', rollout(SESSION, 'needle', '/workspace'))
        self.mapping()
        db = sqlite3.connect(self.discord / 'bridge.sqlite')
        self.addCleanup(db.close)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('INSERT INTO threads VALUES (?,?,?,?)', ('201', '100', SESSION, '/work/discord-project'))
        db.commit()
        paths = [self.discord / 'bridge.sqlite', self.discord / 'bridge.sqlite-wal']
        before = {p.name: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in paths}
        inventory = {p.name for p in self.discord.iterdir()}
        result, data = self.run_search('needle')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(data['matches'][0]['thread_ids'], ['200', '201'])
        self.assertEqual(before, {p.name: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in paths})
        self.assertEqual(inventory, {p.name for p in self.discord.iterdir()})

    def test_event_only_codex_format_is_used_when_no_display_messages_exist(self):
        self.write(self.codex / 'legacy.jsonl', [
            {'type': 'session_meta', 'payload': {'id': SESSION, 'cwd': '/work/project'}},
            {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': '# AGENTS.md instructions\ninjected'}]}},
            {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'needle'}},
        ])
        result, data = self.run_search('needle')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(data['matches']), 1)

    def test_unreadable_discord_state_preserves_other_results_as_partial_json(self):
        self.write(self.codex / 'normal.jsonl', rollout(SESSION, 'needle'))
        self.discord.mkdir(parents=True)
        self.discord.chmod(0)
        try:
            result, data = self.run_search('needle')
        finally:
            self.discord.chmod(0o700)
        self.assertEqual(result.returncode, 2)
        self.assertEqual([m['origin'] for m in data['matches']], ['codex'])
        self.assertTrue(data['coverage']['problems'])

    def load_helper(self):
        spec = importlib.util.spec_from_file_location('history_search_fixture', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_fifo_is_rejected_without_a_blocking_stream_open(self):
        path = self.codex / 'fifo.jsonl'
        path.parent.mkdir(parents=True)
        os.mkfifo(path)
        helper = self.load_helper()
        original = Path.open
        def forbid_fifo_open(p, *args, **kwargs):
            if p == path:
                raise AssertionError('A regular blocking stream open would hang on this FIFO')
            return original(p, *args, **kwargs)
        with patch.object(Path, 'open', forbid_fifo_open):
            data = helper.search('needle', self.home, self.home / '.codex', self.discord)
        self.assertEqual(data['matches'], [])
        self.assertTrue(any(p['kind'] == 'non_regular_file' for p in data['coverage']['problems']))

    def test_regular_file_swapped_to_fifo_before_open_is_rejected(self):
        path = self.write(self.codex / 'swap.jsonl', rollout(SESSION, 'needle'))
        helper = self.load_helper()
        original_open = os.open
        original_stream = Path.open
        def swap_then_open(p, flags, *args, **kwargs):
            if Path(p) == path or (p == path.name and kwargs.get('dir_fd') is not None):
                path.unlink()
                os.mkfifo(path)
                self.assertTrue(flags & os.O_NONBLOCK)
            return original_open(p, flags, *args, **kwargs)
        def forbid_stream(p, *args, **kwargs):
            if p == path:
                raise AssertionError('Missing nonblocking descriptor verification')
            return original_stream(p, *args, **kwargs)
        with patch.object(os, 'open', swap_then_open), patch.object(Path, 'open', forbid_stream):
            data = helper.search('needle', self.home, self.home / '.codex', self.discord)
        self.assertEqual(data['matches'], [])
        self.assertTrue(any(p['kind'] == 'non_regular_file' for p in data['coverage']['problems']))

    def test_derived_roots_must_stay_within_their_trusted_base(self):
        external_temp = tempfile.TemporaryDirectory()
        self.addCleanup(external_temp.cleanup)
        external = Path(external_temp.name)
        self.write(external / 'log.jsonl', rollout(SESSION, 'outside-needle', '/outside'))
        for kind in ['codex', 'claude', 'channels', 'channel', 'codex-state']:
            with self.subTest(kind=kind):
                root_temp = tempfile.TemporaryDirectory()
                self.addCleanup(root_temp.cleanup)
                home = Path(root_temp.name)
                state = home / '.local/state/codex-discord'
                codex = home / '.codex'
                if kind == 'codex':
                    path = codex / 'sessions'
                elif kind == 'claude':
                    path = home / '.claude/projects'
                elif kind == 'channels':
                    path = state / 'channels'
                elif kind == 'channel':
                    path = state / 'channels/100'
                else:
                    path = state / 'channels/100/codex'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(external, target_is_directory=True)
                # An escaped channel can itself contain otherwise well-formed derived roots.
                self.write(external / '100/codex/sessions/log.jsonl', rollout(SESSION, 'outside-needle'))
                self.write(external / 'codex/sessions/log.jsonl', rollout(SESSION, 'outside-needle'))
                self.write(external / 'sessions/log.jsonl', rollout(SESSION, 'outside-needle'))
                data = self.load_helper().search('outside-needle', home, codex, state)
                self.assertEqual(data['matches'], [])
                self.assertTrue(any(p['kind'] == 'outside_history_roots' for p in data['coverage']['problems']))

    def test_cross_root_leaf_alias_keeps_the_actual_discord_origin(self):
        target = self.write(self.discord / 'channels/100/codex/sessions/actual.jsonl', rollout(SESSION, 'needle', '/workspace'))
        self.codex.mkdir(parents=True)
        (self.codex / 'alias.jsonl').symlink_to(target)
        self.mapping()
        _, data = self.run_search('needle')
        self.assertEqual(len(data['matches']), 1)
        self.assertEqual(data['matches'][0]['origin'], 'discord')
        self.assertEqual(data['matches'][0]['channel_id'], '100')
        self.assertEqual(data['matches'][0]['cwd'], '/work/discord-project')

    def test_ancestor_swapped_to_external_symlink_before_open_is_rejected(self):
        path = self.write(self.codex / 'day/log.jsonl', rollout(SESSION, 'inside'))
        external_temp = tempfile.TemporaryDirectory()
        self.addCleanup(external_temp.cleanup)
        external = Path(external_temp.name)
        self.write(external / path.name, rollout(SESSION, 'outside-needle', '/outside'))
        helper = self.load_helper()
        original_open = helper.open_regular
        swapped = False
        def swap_then_open(p, *args, **kwargs):
            nonlocal swapped
            if p == path:
                path.parent.rename(self.codex / 'original-day')
                path.parent.symlink_to(external, target_is_directory=True)
                swapped = True
            return original_open(p, *args, **kwargs)
        with patch.object(helper, 'open_regular', swap_then_open):
            data = helper.search('outside-needle', self.home, self.home / '.codex', self.discord)
        self.assertTrue(swapped, 'Race must occur after discovery and stat, before the actual open')
        self.assertEqual(data['matches'], [])
        self.assertTrue(data['coverage']['problems'])


if __name__ == '__main__':
    unittest.main()
