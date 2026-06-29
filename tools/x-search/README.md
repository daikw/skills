# x-search

CLI wrapper for the xAI [`x_search`](https://docs.x.ai/developers/tools/x-search)
Agent Tool. PEP 723 single-file Python — `uv` resolves `httpx` from the
inline metadata, so no manual venv setup is needed.

## Install

```sh
mkdir -p ~/.local/bin
cp x-search ~/.local/bin/
chmod +x ~/.local/bin/x-search
```

Make sure `~/.local/bin` is on your `PATH`, and that `uv` is installed:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh   # https://docs.astral.sh/uv/
```

## Credentials

`x-search` resolves credentials internally. It accepts a directly exported
`XAI_API_KEY`, and also bootstraps `dotenvx` with `DOTENV_PRIVATE_KEY` to
decrypt `~/.config/dotenvx/.env` when needed.

```sh
x-search search "claude code 4.7" -n 10
```

## Usage

```sh
x-search search "<query>" [-n 1..30] [--language ja] [--from-date YYYY-MM-DD] [--to-date YYYY-MM-DD] [--format markdown|json]
x-search user   <@username> [-n 1..30] [--filter "<topic>"] [--from-date ...] [--to-date ...] [--format ...]
```

See [`../../skills/x-search/SKILL.md`](../../skills/x-search/SKILL.md) for
the Claude Code skill that drives this CLI.

## Pricing

xAI bills two axes independently — tokens and the server-side `x_search`
tool call. As of 2026-05:

- grok-4.3 tokens: \$1.25 / \$2.50 per 1M (in / out)
- `x_search` tool fee: \$5 per 1K calls (= \$0.005/call)

Expect ~1–6 JPY per query depending on complexity.
