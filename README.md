# daikw/skills

Personal Claude Code and Codex skills marketplace by [daikw](https://github.com/daikw).

## Install

### Codex

Add the local marketplace:

```sh
ghq get daikw/skills
codex plugin marketplace add ~/ghq/github.com/daikw/skills
```

Install the plugin:

```sh
codex plugin add daikw-skills@daikw-skills
```

After installing or updating, start a new Codex thread so the skill list is rebuilt.

### Claude Code

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
├── .agents/
│   └── plugins/
│       └── marketplace.json    # Codex local marketplace manifest
├── .claude-plugin/
│   └── marketplace.json        # Claude Code marketplace manifest
├── skills -> plugins/daikw-skills/skills
│                               # compatibility symlink
├── plugins/
│   └── daikw-skills/
│       ├── .codex-plugin/
│       │   └── plugin.json     # Codex plugin manifest
│       └── skills/             # canonical skill source
│           └── <skill-name>/
│               └── SKILL.md
└── tools/                      # bundled CLIs that skills depend on (optional)
    └── x-search/
```

## Development

Local edits reflect through the local marketplace. For Codex, reinstall the
plugin and start a new thread after changing plugin metadata or skills. For
Claude Code, push changes to `main` and run
`claude plugin marketplace update daikw-skills` on other hosts to sync.

## Dotfiles boundary

This repository owns skill content and plugin marketplace metadata. Dotfiles
or chezmoi should own only machine bootstrap steps, such as cloning this repo,
adding the Codex marketplace, and installing the plugin. Avoid duplicating
`plugins/daikw-skills/`, `.agents/plugins/marketplace.json`, or
`.claude-plugin/marketplace.json` in dotfiles; that keeps this repo as the
source of truth and avoids stale copies.

## License

MIT (see [LICENSE](./LICENSE)).
