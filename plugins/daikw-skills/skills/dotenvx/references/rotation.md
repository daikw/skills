# Rotation and recovery

The invariant is that each running, queued, retried, and rollback revision can obtain the private key matching its ciphertext. Updating the shared CI secret first can break old revisions; merging new ciphertext first can break new ones. There is no universally safe fixed ordering.

## Prepare a reviewable change

1. Identify the exact environment file, current key store, consumers, deployment revision, CI scope, and recovery owner. Confirm what the user has authorized: local preparation, remote secret update, credential revocation, merge, and deployment are distinct operations.
2. Preserve existing source changes and the current ciphertext/key pair in approved private recovery storage. Do not place private keys in a branch, commit message, environment dump, or agent-visible command argument. Record only nonsecret identifiers. If the old key is compromised, recovery may require forward repair with new provider credentials instead of restoring compromised credentials.
3. Select the rotation mechanism from the installed release's command help and matching official source. Some releases document `dotenvx rotate -f <file>` and `-fk <key-file>`; verify availability and affected files before use. If unsupported, prepare a version-specific migration plan instead of improvising decrypt/delete-public-key/encrypt on tracked files.
4. Generate the new ciphertext/key pair in an isolated protected workspace using the supported mechanism. Retain complete before/after pairs. Determine which key-store files the operation updates and verify it did not mutate other environments. Test decryption with a controlled key source, strict failures, and value-free validation. A success message or changed public key is insufficient evidence.
5. Build a cutover plan from the deployment system's actual behavior. Prefer revision-scoped secret versions or separately configured deployment slots, with each consumer explicitly mapped to its matching key. An arbitrary `_NEW` variable does not make dotenvx accept both keys. Where revision-scoped pairing is unavailable, coordinate consumers and queued jobs for an authorized cutover with a tested recovery path.

## Apply only the authorized cutover

Present the target, changed files, affected consumers, cutover sequence, validation evidence, and recovery path before any still-unapproved external change. Existing explicit approval for those actions remains valid; do not ask again merely because this reference contains a gate.

Transfer keys directly from protected local storage or an approved secret manager through the receiving tool's supported secret-safe input. Do not extract a key into chat, print it, or pass it via `--body <value>` / command-line environment assignments. Verify the destination repository and environment before writing. A CLI login does not authorize every repository or environment it can access.

Commit only the reviewed encrypted configuration and related nonsecret integration changes. Merge and deploy only within explicit authorization. Do not use automatic merge as part of a generic rotation recipe. Verify actual consumer health on the intended revision and inspect the state of in-flight jobs before declaring the cutover complete.

## Retire and recover

- On failure, stop advancing the cutover. Re-establish a complete matching pair through the approved rollback or forward-repair path; do not repeatedly overwrite a shared secret hoping a different order works.
- After verified cutover, retire the old operational key only when its remaining consumers and recovery requirements have been resolved. Restrict any retained recovery copy to the approved private store and retention policy.
- Avoid plaintext backups. If plaintext was unavoidable, inventory its exact locations, permissions, editor copies, and backups without exposing contents. Clean only identified task-owned files under the agreed policy after recovery is secured; do not blindly delete a `.bak` path. Ordinary deletion is not proof of secure erasure from snapshots or storage media.
- If a private key leaked, old ciphertext in Git history remains decryptable. Rotate or revoke the underlying provider credentials within authorization as well; re-encrypting the same values does not revoke them. History rewriting is a separate, explicitly authorized operation and does not replace credential revocation.

Report local validation, external secret update, merge, deployed health, provider revocation, and retirement separately, with any incomplete stage explicit. Do not call preparation alone a completed rotation.
