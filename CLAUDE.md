# daikw/skills

Personal Claude Code / Codex CLI skills marketplace. Public repository — do not
commit machine-specific values, personal identifiers, or internal hostnames.

## Layout

- `plugins/daikw-skills/skills/<name>/` — canonical skill source (SKILL.md + `references/` `scripts/` `assets/`)
- `skills/` at repo root — compatibility symlink to `plugins/daikw-skills/skills/`
- `.claude-plugin/marketplace.json` / `.agents/plugins/marketplace.json` — marketplace manifests, both point `source` at `./plugins/daikw-skills`
- `tools/<cli-name>/` — CLIs a skill depends on and bundles directly

See [README.md](README.md) for install/update commands.

## Before committing a change under `plugins/daikw-skills/skills/`

Any addition, edit, deletion, or rename of a skill in this repository must go
through the `daikw:meta-rules` checklist (placement judgment, frontmatter and
description rules, rename/migration and delisting checks) before committing:

```sh
plugins/daikw-skills/skills/meta-rules/scripts/lint.sh <skill-name>   # or no args for all skills
```

`lint.sh` only catches what's machine-checkable (frontmatter/name match,
allowed-tools validity, referenced-path existence, supply-chain
contradictions, description length). It does not replace the judgment calls in
`daikw:meta-rules` (placement axis, rename impact, public-repo sensitivity
check) — run both.
