# daikw/skills

Personal Claude Code skills marketplace by [daikw](https://github.com/daikw).

## Install

### Add the marketplace

```sh
ghq get daikw/skills
claude plugin marketplace add ~/ghq/github.com/daikw/skills
```

Or directly from GitHub:

```sh
claude plugin marketplace add daikw/skills
```

### Enable the plugin

```sh
claude plugin install daikw@daikw-skills
```

After enabling, available skills appear as `daikw:<skill-name>` in Claude Code.

## Layout

```
daikw/skills/
├── .claude-plugin/
│   └── marketplace.json        # marketplace manifest
├── skills/                     # canonical skill source
│   └── <skill-name>/
│       └── SKILL.md
└── tools/                      # bundled CLIs that skills depend on (optional)
    └── x-search/
```

## Development

Local edits reflect immediately if the marketplace was added via local path.
Push changes to `main` and run `claude plugin marketplace update daikw-skills`
on other hosts to sync.

For porting these skills to Codex CLI's `.agents/skills/` layout, see
[#1](https://github.com/daikw/skills/issues/1).

## License

MIT (see [LICENSE](./LICENSE)).
