# Environment operations

## Establish the target

Inspect the installed version and relevant command help without loading secrets. Reuse the project's pinned installation. If installation is needed, verify the official package identity, exact release, provenance, and lifecycle scripts before changing the manifest and lockfile together; retain install-script protections. Do not treat a package-manager name or an old example version as a security attestation.

Confirm the intended environment filenames and key source without opening their values. The encrypted `.env` format uses a public encryption key in the file and a separate private decryption key. `.env` maps to `DOTENV_PRIVATE_KEY`; `.env.production` maps to `DOTENV_PRIVATE_KEY_PRODUCTION`. An existing `.env.vault` / `DOTENV_KEY` setup is a different format: establish the existing consumer contract before migration.

Dotenvx uses ECIES with secp256k1 key agreement and AES-256-GCM authenticated encryption. Let the supported implementation generate keys and ciphertext; do not replace it with shell transformations or custom cryptography. Encryption protects values at rest, not an authorized process that already receives plaintext. See the [official cryptographic design](https://dotenvx.com/dotenvx.pdf).

## Load and verify

Use an explicit file and strict failure behavior for required configuration:

```bash
# The application must validate its required variables without logging values.
dotenvx run -f .env.production --strict -- node index.js

# Defaults: existing process variables win, then the first file that defines a key.
dotenvx run -f .env.local -f .env --strict -- npm run dev
```

`--overload` changes precedence: subsequent files can replace earlier and inherited values. Use it only when that override is the intended contract. Confirm precedence with synthetic values in an isolated fixture if the current failure depends on it; do not print live values to compare them. [Upstream precedence reference](https://github.com/dotenvx/dotenvx#run)

For a scoped readability/presence check, discard both streams and expose only status:

```bash
if dotenvx get DATABASE_URL -f .env.production --strict >/dev/null 2>&1; then
  printf '%s\n' 'Required configuration is readable'
else
  printf '%s\n' 'Required configuration check failed' >&2
  exit 1
fi
```

This check does not validate a nonempty value, URL schema, service access, or correct deployment. Use the consumer's existing validation for those requirements. For a ciphertext/key-pair check, isolate it from inherited application variables and unintended key sources so they cannot mask a mismatch.

`run --strict` fails on missing files and decryption errors; `get KEY --strict` also fails on a missing key. Preserve failure status and stop dependent work. Do not add `--ignore`, `|| true`, or fallback credentials to make the check pass. If the installed release lacks required strict behavior, establish equivalent fail-closed behavior before using real secrets. Diagnose with public error categories and synthetic input; do not return raw stderr, secret fragments, or hashes of secrets. [Run failures](https://dotenvx.com/docs/cli/run-strict/), [key-check failures](https://dotenvx.com/docs/cli/get-key-strict/)

## Encrypt or edit encrypted files

Before mutation, confirm the exact file, trusted input, expected key store, permissions, and recovery copy. Ensure `.env.keys`, plaintext inputs, temporary files, editor backups, and private-key exports are excluded from Git; ignore rules do not remove already tracked files.

Use the installed release's supported `encrypt -f <file>` operation within that scope. Keep stdout/stderr out of tool output if that release prints key material or export instructions; report a sanitized status instead. Verify all intended secrets are encrypted and the matching key can decrypt them, without printing values. Existing plaintext exclusions and names ending in `_PLAIN` require explicit review before committing the encrypted file.

Prefer runtime decryption. `decrypt -f <file>` writes plaintext: use it only when plaintext output is itself required, in a protected private location with a recovery and cleanup plan. Never decrypt the tracked working file just to inspect configuration, and never remove its public-key line to invent a rotation procedure.

## CI integration

Use the repository's existing pinned installation and trusted workflow. Supply only the matching private key through the selected repository/environment secret store to the approved consumer. `.env.keys` does not belong in an image, checkout artifact, cache, or deployment bundle. Do not expose production keys to untrusted pull-request code.

Use `run --strict` and a command whose logs have been checked for secret exposure. Secret masking is additional protection, not permission to print values. Preparing workflow changes is separate from updating remote secret values or deploying; those changes need authorization for the specific repository, environment, and operation. After an authorized change, verify the deployed revision and consumer health independently of the secret-upload result.
