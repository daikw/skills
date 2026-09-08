---
name: dotenvx
description: "Configures and troubleshoots dotenvx encryption, environment loading, key rotation, and CI integration when the project uses dotenvx or the user requests it. General environment-variable questions and unrelated secret-manager operations are 対象外."
---

# dotenvx

Make the intended environment available to the authorized consumer, with secrets kept out of agent output and version control. Work from the project's installed dotenvx release, file layout, and deployment contract.

**Freedom Level: mixed.** Choose the investigation and integration approach from the task. Preserve exact key/file mapping, precedence, failure handling, authorization, and recovery boundaries below; these are not optional optimizations.

## Boundaries

- Identify the repository, environment file, consumer, and key source before reading values or making changes. Discover names and metadata first; do not dump environment files, `.env.keys`, process environments, or secret-manager contents.
- Secret values may pass through the existing trusted runtime or secret store, not through chat, tool output, command arguments, diffs, or logs. `--quiet` only reduces logging; it does not redact values. Do not use `get` or `keypair` to display secrets.
- Treat `.env` as active configuration: dotenvx can expand variables and execute command substitutions. Confirm its trusted origin before loading it; do not source or evaluate an untrusted file to inspect it.
- Local preparation does not authorize CI secret writes, deployment, merge, history rewriting, or provider credential changes. Use explicit authorization already present in the conversation for the exact target and operation; otherwise prepare the change and obtain it before that operation.
- Preserve existing source changes and a recoverable ciphertext/key pair before mutation. Keep private keys and any unavoidable plaintext owner-readable only, outside version control and shared artifacts.

## Choose the needed reference

| Task | Read |
|---|---|
| Load variables, diagnose precedence/decryption, encrypt a file, or wire CI | [Environment operations](references/operations.md) |
| Change encryption keys or respond to suspected exposure | [Rotation and recovery](references/rotation.md) |

Read only the reference needed for the task. For an installed-version discrepancy, consult that release's help or official source before choosing commands.

## Completion evidence

Report the environment/file identity, installed version, changed paths, authorization scope for external changes, and secret-free pass/fail results. A presence check does not establish application correctness; a local decryption check does not establish deployed health. Leave any unverified deployment or recovery step explicit.

## Official sources

- [Project source and CLI reference](https://github.com/dotenvx/dotenvx)
- [Encrypted environment and private-key placement](https://dotenvx.com/docs/quickstart/encryption/)
- [Private-key naming](https://dotenvx.com/docs/env-keys-file/)
- [Strict run failures](https://dotenvx.com/docs/cli/run-strict/)
- [Strict key checks](https://dotenvx.com/docs/cli/get-key-strict/)
- [Cryptographic design](https://dotenvx.com/dotenvx.pdf)
