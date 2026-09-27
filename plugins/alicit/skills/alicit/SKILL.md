---
name: alicit
description: Use whenever a human or agent command needs GitHub, cloud, infrastructure, object-storage, or 1Password credentials, or when an `alicit:` failure occurs. Enforces scoped Alicit profiles, approval justifications, and sanitized issue reporting; replaces bao-exec and ambient bearer tokens.
---

# Alicit credentialed commands

Route every credentialed command through Alicit. Never use `bao-exec`, a normal
OpenBao login, an ambient token file, or a bearer token copied into the command
environment.

An Operator Session comes first from a Session Request on the Trusted Host.
If that fails, the CLI tries the alicit Vault's own OIDC login on the `google`
mount: a browser callback, then a device flow that prints a URL and a code.
`ALICIT_LOGIN_CHAIN` changes this order. No Google client lives on the host:
the local Keychain client and `scripts/configure-local-google-device.sh` were
removed on 2026-09-07. If a login fails, report it to the Operator.
Do not retrieve the Kubernetes Secret or export OAuth values yourself.

Before selecting a command, read [global CLI use and release freshness](references/global-cli.md)
when checking installed capabilities, upgrading, or finishing a stable release.
The agent-facing executable must be qualified and current for each stable release;
source changes and published archives alone do not update it.

## Run a command

1. Choose a configured Profile for the task. Prefer an existing exact Profile,
   but do not block on creating one: the Operator-authorized broad proposal
   Profiles are an accepted default when narrower coverage is absent. Read
   [broad credential proposals](references/operator-proposals.md) when using
   `operator-credentials`, `github-operator-all`, or `operator-proposals`. For
   new backend roles, permission sets, native operations, or secret-name inventory,
   use [native Provider proposals](references/provider-proposals.md): an existing
   role or per-task Profile is not required. Do not invent a Profile;
   use `alicit discover --json` when the CLI and Vault support discovery, or
   inspect repository configuration. Discovery uses the bound Operator Session
   and returns configuration metadata without a Mint. The older catalog has
   `configured_profiles` coverage; v2 also exposes capability definitions with
   `configured_profiles_and_capabilities` coverage. V3 adds configured Provider
   mounts, including those without published capabilities; read the
   [inventory contract](references/discovery.md) when interpreting those results.
   No catalog is an access grant or proof of Provider readiness. When `explicit_requests` is `unavailable`,
   capability metadata does not provide a usable Profile-free command. When it
   reports `single_operation`, read [explicit access](references/explicit-access.md)
   for the request format and deployment requirements. If neither source
   identifies usable authority, report the missing Provider or credential set.
   Existing broad proposal Profiles do not require another per-task Profile PR.
2. Select the shortest practical TTL. Omit a TTL override when the server-owned
   default is already sufficient.
3. Write one reviewable justification of 16–500 bytes. Name the task, target,
   and why each requested scope is necessary. Do not include secrets or
   speculative future work.
4. Run the command in this shape:

   ```sh
   alicit run \
     --profile github-issues \
     --ttl github-issues=5m \
     --justification "Create one triaged issue in alicit-ai/alicit for the reproduced CLI failure" \
     -- gh issue create --repo alicit-ai/alicit ...
   ```

5. Confirm that the approval surface shows the expected provider, profiles,
   TTL, exact operation, and justification before approving.

Each `alicit run` can wake the Operator's phone for one approval, so plan the
commands of one task together and do not poll. A `gh` command still needs its
own invocation: a `gh` inside `bash -c` does not get the approved token, and it
can silently run as a stored `gh` login (see the adapter limits below). The CLI writes Mint progress to stderr, so redirect only stdout
to a data file: `> out.json`, not `> out.json 2>&1`.

For issue and label work, prefer the repository-exact shortcut:

```sh
alicit github \
  --justification "Read the complete issue backlog in darren-iac/iac for repository grooming" \
  -- issue list --repo darren-iac/iac --state all
```

For recognized `gh issue`, `gh label`, and repository-scoped issue or label API
commands, the CLI selects the five-minute `github-repository-exact` Profile and
derives `issues=read` or `issues=write`. The Provider POST body freezes one
configured owner and one repository. The supported installations are
`alicit-ai`, `darrengruber`, `darren-iac`, `fourslide`, and `claudefirm`; repositories under
those owners do not need a per-repository Alicit Profile. The Justification must
name the exact repository.

For other routine GitHub repository work that has no narrower Profile, use the
short broad route:

```sh
alicit github \
  --justification "Use installation-wide GitHub authority to list pull requests in darrengruber/pippin for the current review" \
  -- pr list --repo darrengruber/pippin --json number,title
```

The Justification must contain the words "installation-wide GitHub
authority"; the CLI refuses it otherwise. It fixes `github-operator-all` and a
five-minute Invocation, requires the same
explicit Git Target as the generic `gh` adapter, and passes the Mint
through the active Policy and je valide path. The GitHub App token remains
installation-wide. jev is a Witness and Cedar decides; neither turns this broad
credential into exact command confinement. Production je valide is on by
default and the shortcut has no client-side opt-in or opt-out; failure or low
confidence takes the ordinary Operator wake. Prefer a repository-scoped Profile or
the controlled Git/PR adapters whenever one covers the work.

The shortcut accepts `gh api` only under a repository's issues or labels path.
For any other API read, name the Profile yourself and put the endpoint right
after `api`:

```sh
alicit run --profile github-operator-all --ttl github-operator-all=5m \
  --justification "Use installation-wide GitHub authority to read the jobs of CI run <id> in alicit-ai/alicit" \
  -- gh api repos/alicit-ai/alicit/actions/runs/<id>/jobs --method GET
```

The Alicit GitHub Apps have no `checks` permission, so check-runs endpoints
return 403. Read CI state from the Actions runs and jobs endpoints. Each call
wakes the Operator, so read once after a local signal instead of polling.

The production Policy excludes every configured `testflight` and
`*-testflight` release Profile from je valide release. Shipping a build always
wakes an Operator. The separate `*-testflight-import` Profiles rotate signing
material without shipping and remain jev-eligible.

For authenticated Git transport, use the shortcut so the CLI selects the
narrowest static Git Target when one exists, otherwise the five-minute
repository-exact Profile:

```sh
alicit git \
  --justification "Push the reviewed alicit change to alicit-ai/alicit destination refs/heads/main" \
  -- push https://github.com/alicit-ai/alicit.git HEAD:refs/heads/main
```

Local Git operations need no credential and run normally. Under the five
configured installations, a repository needs no per-repository Profile:
`fetch` derives `contents=read` and `push` derives `contents=write`. The
shortcut keeps the transport boundary at one repository, `fetch` or `push`,
one explicit refspec, and no force or delete operation. A workflow-file push
that needs `workflows=write` must use separately reviewed authority.

For controlled PR commands, read [the PR workflow](references/pull-requests.md)
before choosing Profiles or command flags. This route requires a compatible
Vault and delivered v4 Apple Approvers; it executes the reviewed request without
starting `gh`. Other `gh` commands use the credential adapter described below.

The exact-repository route supersedes repository-only issue Profiles for normal
issue and label work. Existing static Profiles remain useful where they impose
a narrower operation or destination boundary. The four
`github-openbao-plugin-secrets-<plugin>-pr-read` Profiles read pull requests on
the Cloudflare, LiteLLM, OmniRoute and RustFS plugin repositories, and grant no
write permission. A Profile used against a repository its
permission set does not name mints a valid token, and GitHub then reports
`Could not resolve to a Repository`. That message means the permission set does
not name that repository, not that the repository is missing.

ADR-0079 keeps the broad proposal Profiles available when no narrower Profile
covers the work, so `github-operator-all` remains a legitimate fallback for
commands outside the exact issue/label and controlled Git/PR adapters. Treat it
as a fallback: it is installation-wide even when the command names one repo.

A `gh api` command must name its HTTP method with `--method` whenever it passes
`-f`, `-F`, `--field`, `--raw-field` or `--input`. Those flags make `gh` send a
POST, and Alicit rejects the command rather than approve a write that reads
like a read.

Four GitHub adapter limits fail quietly or with a misleading message:

- `gh pr checks` fails with `Resource not accessible by integration`
  (`statusCheckRollup`): the App token cannot read check rollups. Read CI with
  `gh run list --branch <branch>` and `gh run view <id> --json jobs` instead.
- `alicit github -- api repos/<owner>/<repo>/actions/...` is refused with
  `API endpoint must stay under the target repository's issues or labels path`,
  because the shortcut treats `gh api` as issue work. Use
  `alicit run --profile github-operator-all -- gh api ...` for other endpoints.
- A `gh` started inside `sh -c` does not get the approved token: the adapter
  prepares only a `gh` that is the direct child. On a host with a stored `gh`
  login, the nested `gh` silently runs as that login, outside the approval
  (#198). On a host without one, its output is empty, not an error. Never nest
  `gh` in a shell: loop in the outer shell and start one
  `alicit run -- gh ...` per call.
- An API call outside one repository, such as `gh api orgs/<org>/repos` to
  create a repository, is refused before approval: the adapter needs a
  `repos/<owner>/<repo>/...` endpoint right after `api`. No Profile creates a
  repository. Ask the Operator to create it, then push through `alicit git`.

The child process receives only an invocation-local loopback proxy capability.
For a command whose executable is `gh`, exactly one requested profile must be
named `github-<permission-set>`. Alicit obtains the dynamic GitHub token from
the owner-scoped `/v1/github/<owner>/token/<permission-set>` route through that
proxy after exact-operation approval. The command must name its target with
`--repo <owner>/<repository>` (or an owner-scoped `repos/<owner>/<repository>/...`
`gh api` endpoint); Alicit rejects missing or conflicting targets before
authentication. It replaces ambient GitHub token variables, isolates the normal
`gh` credential store, and exposes only that approved provider token to `gh`.
The adapter currently targets `github.com`; do not use it for a GitHub
Enterprise host. Do not print, persist, or try to recover either credential.

Authenticated Git transport is deliberately narrower than the general GitHub
CLI adapter. It supports only one explicit fetch or push refspec. A static Git
target can further restrict destinations; otherwise the dynamic target binds
the exact owner, repository, action, and Provider body. There is no owner-wide
Git token: authority for one repository says nothing about another repository
of the same owner.

| Repository | Action | Permitted destinations | Profile |
|---|---|---|---|
| `alicit-ai/alicit` | fetch | `refs/*` | `github-alicit-git-read` |
| `alicit-ai/alicit` | push | `refs/heads/*`, `refs/tags/*` | `github-alicit-git-write` |
| `darrengruber/scrim` | fetch | `refs/*` | `github-scrim-git-read` |
| `darrengruber/scrim` | push | `refs/heads/main` | `github-scrim-git-write` |
| any other repository under a configured owner | fetch | one explicit `refs/*` destination | `github-repository-exact` |
| any other repository under a configured owner | push | one explicit branch or tag destination | `github-repository-exact` |

Run `alicit discover` to read the configured targets and their TTL ceilings.
That list is configuration, not authorization.

The justification must name the operation, the repository, and its
exact destination ref:

```sh
alicit run \
  --profile github-alicit-git-write \
  --ttl github-alicit-git-write=5m \
  --justification "Push the reviewed Alicit change to alicit-ai/alicit destination refs/heads/main" \
  -- git push https://github.com/alicit-ai/alicit.git HEAD:refs/heads/main
```

The second target uses its own Profile and its own destination:

```sh
alicit run \
  --profile github-scrim-git-write \
  --ttl github-scrim-git-write=5m \
  --justification "Push the reviewed change to darrengruber/scrim destination refs/heads/main" \
  -- git push https://github.com/darrengruber/scrim.git HEAD:refs/heads/main
```

Use the Profile of the target you name. A Profile for one target cannot carry
work on another, and `github-operator-all` is not a Git push path at all. A
push to a destination ref the target does not permit fails before Alicit
releases any credential.

Alicit rejects implicit, cross-repository, force and delete refspecs before
authentication. It replaces ambient GitHub credentials with a single-use
askpass boundary and removes the helper after the command. Never use an
ambient Git credential helper or a direct authenticated push.

The new controlled adapter freezes the source object and peeled commit before
authentication and signs the Git inputs in a v3 approval. Its private transport
configuration ignores local refs, hooks, URL rewrites and Git environment
overrides. Fetch updates the named local destination only if it is unchanged
and not checked out. If that final update fails, objects may have been fetched
without changing the destination. The compatible Apple build and Git-aware live
schema must be delivered before enabling this route; the installed trusted CLI
must not be replaced merely to try an undelivered protocol. The source
repository records this protocol in ADR-0059 and its operations runbook.

## Triage a failed request

Treat approval and provider readiness as separate gates. A human decision can
authorize only the exact request it names; it cannot repair missing live
profiles, permission sets, or provider material.

1. Record the request ID and its terminal outcome before retrying. A declined,
   expired, or otherwise terminal request is not revived by a later approval;
   a new invocation creates a new request that needs its own decision.
   If the child prints a successful mutation and only the final `revoke-self`
   cleanup times out, assume the mutation may have happened. Do not repeat it;
   verify with a fresh read-only Invocation and treat the original token as
   live until its short TTL expires.
2. Confirm that the Approver sent a signed decision before diagnosing the
   Provider. If the app fails while the request remains pending, the Provider
   has not run. A local proxy error ending in `poll Control Group approval: HTTP
   404` means the pending request expired; it does not prove a Provider failure.
   Check the Approver's sanitized diagnostic log for a signing failure first.
   `alicit diagnostics --trace <trace-id>` reads the records that the
   Approver, the CLI and `alicit-observe` stored in the alicit Vault for this
   Operator. A failed command prints its `trace_id`. The Operator can press
   **Send to Alicit** on the iPhone Diagnostics screen to upload every
   buffered Approver record again.
   If the device accepts the decision but the Invocation remains `pending` or
   the card remains visible, do not extend polling or wait for expiry. Mint
   request and terminal-result state must survive plugin reloads and backend
   instance changes in OpenBao logical storage. Treat disagreement between the
   device and Invocation as a plugin deployment or storage defect, then create
   one fresh request only after that cause has changed.
   If a native Control Group operation returns HTTP 502 before an Approval card
   exists and the plugin trace reports `operation=requests`, diagnose the
   `auth/alicit/requests` registration path before the protected handler. With
   an active Policy, a legacy native registration has no qualified Mint
   Envelope and must fail closed unless the operation has a deliberately
   bounded migration or recovery path. Inspect the protected effect before any
   retry; a registration failure does not by itself prove whether it committed.
3. Check the server-owned chain independently: the named profile exists, its
   policy targets the mounted backend path, the provider permission set exists,
   and the backing item or provider configuration exists. Policy acceptance
   alone does not prove the provider is ready.
4. Treat missing live state as a bootstrap or persistence incident. A dev-mode
   OpenBao restart can leave repository configuration intact while erasing KV
   data and permission sets. Reconcile the exact missing state instead of
   broadening policy or asking the user to approve repeated identical requests.
5. Retry once the observed cause has changed, then verify the new request ID
   and final provider operation. If the credential plane itself still prevents
   reporting, use the sanitized local handoff below.

On macOS, Keychain status `-25293` after replacing or rebuilding the CLI is an
executable-identity ACL failure, not an absent credential. Keep using the exact
binary that enrolled the Trusted Host, or delete only Alicit's `trusted-host`
and `operator-session` items and repeat Host Enrollment with the replacement.
Never export the stored values to work around the ACL.

Keychain status `-25308` is different: the Keychain is locked and this process
cannot prompt. That is the normal state of a launchd-started runner, not a fault
to repair on the machine. Do not unlock the login Keychain by hand to get a job
moving — a Trusted Host exists to start an Invocation with no Operator present.
Enroll the host instead; the CLI stores its credential in the mode-0600 file
ADR-0026 names and reports the path. Only the Trusted Host credential ever lives
there. See "Headless macOS Trusted Hosts" in `docs/OPERATIONS.md`.

Keychain status `-25300` is a third state, and it is not a fault at all. It is
`errSecItemNotFound`: nothing is stored under that account. After
`alicit report`, it means the Reporter was never configured on this host, and
the command says so:

```text
alicit: load Reporter: credential is absent or unavailable (Keychain status -25300);
        run 'alicit configure reporter --from-file <path|->'
```

Run that `configure` command to fix it, or file through the wrapped
`gh issue create` route below. Do not read `-25300` as a broken or locked
Keychain; neither the `-25293` ACL case nor the `-25308` locked case applies.

For a simulator Approver, keep one explicitly named device and UDID for the
whole diagnostic. Never run a generic test helper that creates disposable
simulators against a live Enrollment. A Debug simulator build must be launched
with `-AlicitSoftwareKey`; `SecureEnclaveSignerError` proves the installed app
cannot use the Enrollment key, not that the Provider rejected the request. If
that inaccessible key also prevents in-app reset, clear only the dedicated
simulator: terminate and uninstall Alicit, reset that simulator's Keychain,
install a normally ad-hoc-signed Debug build, launch it with the software-key
flag, and enroll once. Do not build this recovery app with
`CODE_SIGNING_ALLOWED=NO`, because the resulting linker-signed bundle lacks the
application identity Keychain access needs.

## Report Alicit friction

Treat failures, confusing approval text, missing profiles, excess scope, and
provider-icon mismatches as product feedback.

1. Read [`references/issue-tracker.md`](references/issue-tracker.md) and
   [`references/triage-labels.md`](references/triage-labels.md). These copies
   keep the globally installed skill self-contained; their repository sources
   are under `docs/agents/`.
2. Search open and closed GitHub issues for the symptom and root cause through a
   narrowly justified Alicit GitHub invocation.
3. Add sanitized evidence to a matching issue. When none exists, prepare a
   reviewed body and run:

   ```sh
   alicit report --title "Outcome-oriented failure title" --body-file report.md
   ```

   The command fixes the tracker and the `bug` and `needs-triage` labels. It
   files through the Reporter, the one standing GitHub App credential on the
   host, so it needs no alicit Vault, Approver or Approval. Use
   `--body-file -` for reviewed standard input.

   If `alicit report` is unavailable on this host but GitHub is reachable, for
   example on Keychain status `-25300` above, file through the wrapped CLI
   instead:

   ```sh
   alicit run --profile github-issues --ttl github-issues=5m \
     --justification "Create one triaged issue in alicit-ai/alicit for the reproduced failure" \
     -- gh issue create --repo alicit-ai/alicit --title "..." \
        --label bug --label needs-triage --body-file report.md
   ```

   That route goes through the alicit Vault and an Approval, so it bypasses
   nothing. Use it before the local handoff below, which is for a host that
   cannot reach GitHub at all.
4. Include `alicit version`, platform/architecture, expected and actual
   behavior, the safe command shape, profiles, TTLs, and the exact non-secret
   approval justification.
5. Redact credentials, tokens, device and polling secrets, enrollment codes,
   secret values, and sensitive URLs. Do not paste arbitrary command output
   without reviewing it line by line.

If Alicit authentication is the reason GitHub cannot be reached, do not bypass
the credential plane or recursively invoke Alicit. Save a complete, sanitized,
ready-to-file issue body to
`bug-reports/YYYY-MM-DD-alicit-<short-slug>.md` in the originating repository,
report its absolute path, and keep it there until a maintainer records the
resulting issue URL. This is a durable local handoff, not a successful filing.
