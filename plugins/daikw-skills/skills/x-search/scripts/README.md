# x-search CLI source

This directory contains the historical PEP 723 Python implementation of the xAI x_search CLI.
Its inline `httpx` requirement is a version range. Copying and executing this source can resolve new third-party code; the source is not an approved fresh-install recipe.

## Existing installation

Use the already identified `x-search` executable and its installed command help. Credential resolution belongs to that executable; never print tokens or dotenv private keys for diagnosis.

```text
x-search search <query> [-n 1..30] [--language ja] [--from-date YYYY-MM-DD] [--to-date YYYY-MM-DD] [--format markdown|json]
x-search user <@username> [-n 1..30] [--filter <topic>] [--from-date ...] [--to-date ...] [--format ...]
```

JSON output is requested from the model, not guaranteed to be a raw, validated post array. Parse it and verify claimed sources and timestamps.

## Missing installation

Report the missing prerequisite. Establish a pinned, isolated dependency environment and review the actual source and supply-chain requirements before a separate approved installation. Do not use an unverified remote installer or run this ranged-dependency script merely to make the command available.

## Cost and scope

Select query, dates and result count from the current request. Verify current official pricing when cost changes a decision; old per-query estimates are not current billing evidence.
See [the skill entrypoint](../SKILL.md) for the operation boundary and [xAI documentation](https://docs.x.ai/developers/tools/x-search) for the upstream tool.
