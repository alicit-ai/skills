# Use and maintain the global CLI

## Start with the executable agents actually run

Run `command -v alicit`, `alicit --version`, and `alicit help` before assuming a
source feature is installed. On the release Mac the supported path is
`~/.local/bin/alicit`; inspect its resolved path, SHA-256 and `go version -m`
when it reports `dev`. A successful command from a worktree does not refresh the
global installation. Do not place an experimental binary earlier on PATH.

Use installed help to choose the catalog and Request outcome commands. Where
supported, `alicit doctor --catalog --json` returns metadata without a Request; coverage
is not a grant or readiness proof. Use the narrow server-owned Profile and exact
reviewable operation. Preserve the request ID and terminal outcome before retry;
a lost response is a reason to observe effects, not repeat a mutation.

## Every stable release must refresh the global installation

Treat CLI archives, compatible backend/Approver delivery, and global host promotion
as separate release gates. Each stable release must leave the agent-facing CLI
on that exact tested release, with version/source/hash recorded and a verified
scoped Invocation plus cleanup. Publishing a tag, Homebrew cask or TestFlight
build alone does not satisfy the installed-CLI gate. If host promotion cannot
complete, report the stable release's host-delivery gap explicitly.

Stage the release in a durable owner-controlled location and preserve the prior
binary/account selector for rollback. Use `python3 scripts/stage-cli-release.py
--version <exact-version> --source-commit <reviewed-tag-commit>` on the native Mac
from the release checkout. Its ledger and generated status distinguish verified
staging from promotion; re-run identical inputs to resume. See OPERATIONS
"Verified CLI staging" for prerequisites, rollback inventory and failure recovery. On macOS qualify fresh-process Keychain
reads, Host/Session use, configured Reporter access and a real narrow Invocation
before atomically switching the global executable. Ad-hoc binaries have different
code identities; never overwrite or re-sign the working enrolled executable as
an experiment. Other hosts get the published CLI with
`brew install --cask alicit-ai/tap/alicit`; the cask and a manual install both
download the archives from `https://alicit.ai/download/<tag>/`. Use the repository OPERATIONS CLI-upgrade procedure: explicit
Keychain authorization or a new isolated account/Host Enrollment, without
exporting credentials. Developer ID signing is the intended unattended update
path; its first transition still requires qualification. App signing jobs consume
the qualified installed CLI and must not rebuild it mid-release.

After promotion run the version/identity checks and a scoped operation using plain
`alicit` from an agent shell; verify rollback is usable. Refresh this skill from
its versioned `skills/alicit` source with the supported installer, checking its
packaged references. Never call an installed cache edit a published skill update.

## Provider and transport failures

A successful approval followed by Provider HTTP 500 is not a notification failure.
For Kubernetes TokenRequest credentials, expiration must be at least 600 seconds;
an Invocation may be shorter if the Provider and policy allow it. Verify the
actual issued lifetime and revocation; do not generalize one TTL fix to all 500s.

GitHub repository `.permissions` booleans are not sufficient proof of an App
installation token's effective endpoint permissions. Diagnose the exact denied
endpoint and current server-owned permission set. Before retrying an uncertain
push, verify the remote ref. Do not broaden authority based on a generic 404.
