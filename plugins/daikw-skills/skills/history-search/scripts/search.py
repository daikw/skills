#!/usr/bin/env python3
"""Find conversations across local Codex, Claude Code, and Discord bridge logs.

Only metadata is returned. Source transcripts and bridge databases are never
updated. A search result is a discovery candidate, not an authorship assertion.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys


INJECTED = ('# AGENTS.md instructions', '<environment_context>',
            '<permissions instructions>', '<system-reminder>', '<local-command-stdout>',
            '<local-command-stderr>', '<command-message>')


def string(value):
    return value if isinstance(value, str) and value else None


def visible_text(text, origin):
    if not isinstance(text, str) or text.lstrip().startswith(INJECTED):
        return ''
    if origin.startswith('discord'):
        if text.startswith('Work only in /workspace.'):
            text = text.partition('\n\n')[2]
        if text.startswith('Channel role instructions:\n'):
            text = text.partition('\n\nCurrent user request:\n')[2]
        text = text.partition('\n\nDiscord channel context follows as quoted data')[0]
    return text


def message_text(record, origin):
    if origin == 'claude':
        if record.get('type') not in ('user', 'assistant') or record.get('isMeta') or record.get('isCompactSummary'):
            return []
        message = record.get('message')
        if not isinstance(message, dict):
            return []
        content = message.get('content')
        if isinstance(content, str):
            return [visible_text(content, origin)]
        if isinstance(content, list):
            return [visible_text(block.get('text'), origin) for block in content
                    if isinstance(block, dict) and block.get('type') == 'text']
        return []
    payload = record.get('payload')
    if not isinstance(payload, dict) or record.get('type') != 'response_item' or payload.get('type') != 'message':
        return []
    if payload.get('role') not in ('user', 'assistant') or payload.get('channel') == 'analysis':
        return []
    content = payload.get('content')
    if not isinstance(content, list):
        return []
    return [visible_text(block.get('text'), origin) for block in content
            if isinstance(block, dict) and block.get('type') in ('input_text', 'output_text')]


def problem(problems, kind, path, line=None):
    item = {'kind': kind, 'path': str(path)}
    if line is not None:
        item['line'] = line
    problems.append(item)


def anchored(path, base, problems):
    try:
        canonical, trusted = path.resolve(), base.resolve()
        if canonical == trusted or not canonical.is_relative_to(trusted):
            problem(problems, 'outside_history_roots', path)
            return False
        return True
    except (OSError, RuntimeError):
        problem(problems, 'unreadable_directory', path)
        return False


def roots_for(home, codex_home, state, problems):
    def root(origin, path, anchors, **metadata):
        return {'origin': origin, 'path': str(path), '_anchors': anchors, **metadata}
    roots = [
        root('codex', codex_home / 'sessions', [(codex_home / 'sessions', codex_home)], codex_home=str(codex_home)),
        root('codex-archive', codex_home / 'archived_sessions', [(codex_home / 'archived_sessions', codex_home)], codex_home=str(codex_home)),
        root('claude', home / '.claude/projects', [(home / '.claude/projects', home)]),
    ]
    channels = state / 'channels'
    collection = root('discord', channels, [(channels, state)], collection=True)
    roots.append(collection)
    if not anchored(channels, state, problems):
        collection['status'] = 'error'
    else:
        try:
            children = sorted(channels.iterdir())
        except FileNotFoundError:
            children = []
        except OSError:
            problem(problems, 'unreadable_directory', channels)
            collection['status'] = 'error'
            children = []
        for channel in children:
            if re.fullmatch(r'[1-9][0-9]*', channel.name):
                directory = channel / 'codex'
                roots.append(root('discord', directory / 'sessions',
                    [(channels, state), (channel, channels), (directory, channel), (directory / 'sessions', directory)],
                    codex_home=str(directory), channel_id=channel.name))
    legacy = state / 'codex'
    roots.append(root('discord-legacy', legacy / 'sessions',
                      [(legacy, state), (legacy / 'sessions', legacy)], codex_home=str(legacy)))
    return roots


def open_regular(path, problems, binary=False, base=None):
    descriptor = None
    directory = None
    try:
        # Inputs are canonical discovery paths. Pin each ancestor so a rename and
        # symlink replacement cannot redirect the subsequent file open.
        base = Path(base) if base is not None else path.parent
        relative = path.relative_to(base)
        if not base.is_absolute() or '..' in base.parts + relative.parts:
            raise ValueError('Expected an absolute path within the trusted base')
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory = os.open(base.anchor, flags)
        for component in base.parts[1:] + relative.parts[:-1]:
            child = os.open(component, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(relative.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            problem(problems, 'non_regular_file', path)
            return None
        stream = os.fdopen(descriptor, 'rb' if binary else 'r', encoding=None if binary else 'utf-8')
        descriptor = None
        return stream
    except (OSError, ValueError):
        problem(problems, 'unreadable_file', path)
        return None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if directory is not None:
            os.close(directory)


def bridge_mapping(state, problems):
    path = state / 'bridge.sqlite'
    try:
        if not anchored(path, state, problems) or not path.exists():
            return None
        if not stat.S_ISREG(path.stat().st_mode):
            problem(problems, 'non_regular_file', path)
            return None
        stream = open_regular(path.resolve(), problems, binary=True)
        if stream is None:
            return None
        with stream:
            uses_wal = stream.read(20)[18:20] == b'\x02\x02'
        if uses_wal and not all(Path(str(path) + suffix).is_file() for suffix in ('-wal', '-shm')):
            problem(problems, 'unavailable_bridge_mapping', path)
            return None
        # mode=ro sees live WAL; SQLite may update existing SHM reader bookkeeping.
        with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
            db.execute('PRAGMA query_only=ON')
            rows = db.execute('SELECT id,parent_id,session,workspace FROM threads').fetchall()
        result = {}
        for thread, parent, session, workspace in rows:
            if not all(isinstance(v, str) and v for v in (thread, parent, session)):
                continue
            if not re.fullmatch(r'[1-9][0-9]*', thread) or not re.fullmatch(r'[1-9][0-9]*', parent):
                problem(problems, 'invalid_bridge_mapping', path)
                continue
            result.setdefault(session, []).append((thread, parent, string(workspace)))
        return result
    except (sqlite3.Error, OSError, ValueError):
        problem(problems, 'unavailable_bridge_mapping', path)
        return None


def inspect_file(path, root, query, mapping, problems):
    origin = root['origin']
    result = {'origin': origin, 'path': str(path), 'session_id': None, 'cwd': None}
    if 'codex_home' in root:
        result['codex_home'] = root['codex_home']
    if 'channel_id' in root:
        result['channel_id'] = root['channel_id']
    if origin == 'claude':
        result['project_key'] = path.relative_to(root.get('_canonical', root['path'])).parts[0]
    matched = False
    preferred_messages = 0
    fallback_match = False
    try:
        stream = open_regular(path, problems, base=root['_trusted_base'])
        if stream is None:
            return None
        with stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except (ValueError, UnicodeError):
                    problem(problems, 'invalid_json', path, number)
                    continue
                if not isinstance(record, dict):
                    problem(problems, 'invalid_record', path, number)
                    continue
                payload = record.get('payload')
                if record.get('type') == 'session_meta' and isinstance(payload, dict):
                    result['session_id'] = string(payload.get('id')) or result['session_id']
                    result['cwd'] = string(payload.get('cwd')) or result['cwd']
                if origin == 'claude':
                    result['session_id'] = result['session_id'] or string(record.get('sessionId'))
                    result['cwd'] = result['cwd'] or string(record.get('cwd'))
                texts = message_text(record, origin)
                preferred_messages += any(texts)
                matched |= any(query in text.casefold() for text in texts)
                # Older event-only logs have no response_item message projection.
                if record.get('type') == 'event_msg' and isinstance(payload, dict) and payload.get('type') in ('user_message', 'agent_message'):
                    fallback_match |= query in visible_text(payload.get('message'), origin).casefold()
    except (OSError, UnicodeError):
        problem(problems, 'unreadable_file', path)
    if not (matched or (preferred_messages == 0 and fallback_match)):
        return None
    if origin == 'claude' and result['session_id'] is None:
        result['session_id'] = path.stem
    if origin.startswith('discord'):
        result['recorded_cwd'] = result['cwd']
        result['cwd'] = None
        rows = [] if mapping is None else mapping.get(result['session_id'], [])
        if 'channel_id' in root:
            rows = [r for r in rows if r[1] == root['channel_id']]
        parents = {r[1] for r in rows}
        workspaces = {r[2] for r in rows}
        result['thread_ids'] = sorted({r[0] for r in rows})
        if len(parents) == 1 and len(workspaces) == 1 and None not in workspaces:
            result.update(channel_id=next(iter(parents)), cwd=next(iter(workspaces)), mapping_status='mapped')
        else:
            result['mapping_status'] = 'unavailable' if not rows else 'ambiguous'
    return result


def search(query, home, codex_home, state):
    problems = []
    roots = roots_for(home, codex_home, state, problems)
    mapping = bridge_mapping(state, problems)
    allowed = []
    for root in roots:
        root['files'] = 0
        if root.get('status') == 'error':
            continue
        if not all(anchored(child, base, problems) for child, base in root['_anchors']):
            root['status'] = 'error'
            continue
        directory = Path(root['path'])
        try:
            directory_stat = directory.stat()
        except FileNotFoundError:
            root['status'] = 'missing'
            continue
        except OSError:
            root['status'] = 'error'
            problem(problems, 'unreadable_directory', directory)
            continue
        if not stat.S_ISDIR(directory_stat.st_mode):
            root['status'] = 'error'
            problem(problems, 'not_directory', directory)
            continue
        root['status'] = 'searched'
        if not root.get('collection'):
            root['_canonical'] = str(directory.resolve())
            root['_trusted_base'] = root['_anchors'][0][1]
            allowed.append((directory.resolve(), root))
    seen = set()
    matches = []
    for root in roots:
        if root.get('status') != 'searched' or root.get('collection'):
            continue
        directory = Path(root['path'])
        def onerror(error):
            problem(problems, 'unreadable_directory', error.filename or directory)
        for current, dirs, files in os.walk(directory, onerror=onerror, followlinks=False):
            dirs.sort()
            for name in sorted(files):
                if not name.endswith('.jsonl'):
                    continue
                path = Path(current) / name
                try:
                    canonical = path.resolve()
                    owners = [(base, owner) for base, owner in allowed if canonical.is_relative_to(base)]
                    if not owners:
                        problem(problems, 'outside_history_roots', path)
                        continue
                    owner = max(owners, key=lambda item: (len(item[0].parts), item[1]['origin'].startswith('discord')))[1]
                    file_stat = canonical.stat()
                    if not stat.S_ISREG(file_stat.st_mode):
                        problem(problems, 'non_regular_file', path)
                        continue
                    key = (file_stat.st_dev, file_stat.st_ino)
                    if key in seen:
                        continue
                    seen.add(key)
                    root['files'] += 1
                    result = inspect_file(canonical, owner, query.casefold(), mapping, problems)
                    if result:
                        matches.append(result)
                except (OSError, ValueError, RuntimeError):
                    problem(problems, 'unreadable_file', path)
    for root in roots:
        root.pop('_anchors', None)
        root.pop('_canonical', None)
        root.pop('_trusted_base', None)
    return {'matches': matches, 'coverage': {'roots': roots, 'problems': problems}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home(), help='history owner home; defaults to current home')
    parser.add_argument('--codex-home', type=Path, help='Codex state directory; defaults to CODEX_HOME or HOME/.codex')
    parser.add_argument('--discord-state-dir', type=Path, help='bridge stateDir; defaults to HOME/.local/state/codex-discord')
    parser.add_argument('query', help='literal case-insensitive conversation text; use -- before a leading dash')
    args = parser.parse_args(argv)
    if not args.query.strip():
        parser.error('query must contain a non-whitespace character')
    home = args.home.expanduser().resolve()
    codex_home = (args.codex_home or Path(os.environ.get('CODEX_HOME', home / '.codex'))).expanduser().resolve()
    state = (args.discord_state_dir or home / '.local/state/codex-discord').expanduser().resolve()
    result = search(args.query, home, codex_home, state)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result['coverage']['problems'] else 0


if __name__ == '__main__':
    sys.exit(main())
