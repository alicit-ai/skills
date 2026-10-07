---
name: alicit
description: Use whenever a human or agent command needs GitHub, cloud, infrastructure, object-storage, or 1Password credentials; when configuring a Docker-based GitHub Actions build; or when an `alicit:` failure occurs. Enforces scoped Alicit profiles, approval justifications, and sanitized issue reporting; replaces bao-exec and ambient bearer tokens.
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

The CLI has four verbs (ADR-0120):

| Verb | What it does |
|---|---|
| `alicit run --justification "<why>" -- <command>` | runs one command with one approved credential |
| `alicit enroll` | makes this machine a Trusted Host |
| `alicit help` | prints the version and the usage |
| `alicit doctor [--fix]` | reports what is wrong on this host; never wakes the Operator |

`alicit --version` prints the version. The Operator's admin verbs (Settings,
Policy, Capability Models, Tenants, Allowances, Host invitations, TestFlight)
are in the separate `alicit-ops` binary, and the remote MCP server is
`alicit-mcp`. An Agent needs neither.

`alicit run` starts `alicit enroll` when this machine has no trust yet. When
the Operator Session has expired, it sends a Sign-in Request, waits for the
Operator, and then continues. `alicit doctor` only reads; `alicit doctor --fix`
repairs what it can, which can send a Sign-in Request.

Before selecting a command, read [global CLI use and release freshness](references/global-cli.md)
when checking installed capabilities, upgrading, or finishing a stable release.
The agent-facing executable must be qualified and current for each stable release;
source changes and published archives alone do not update it.

## Docker CI builds

For every Docker or Compose build on Alicit's ephemeral ARC runners, check out
the repository and use `./.github/actions/setup-docker-build`. A pull-only job
passes the read-only `DOCKERHUB_READ_USERNAME` and `DOCKERHUB_READ_TOKEN`; only
an image-publishing job passes the push token `DOCKERHUB_USERNAME` and
`DOCKERHUB_TOKEN`, because a CI job runs pull request code. It authenticates
the fresh DinD daemon before creating Buildx, covering cold base-image and
Compose service-image pulls that BuildKit cannot restore. Pull-only CI treats
unavailable authentication as a warning so a temporary Docker Hub lockout does
not block validation; image-publishing jobs set `dockerhub-login-required:
"true"` and must fail without a working login. A reusable workflow that runs
CI must declare `secrets: inherit` when these repository secrets are needed.

Keep each `docker/build-push-action` cache explicit at its call site with a
dedicated `type=gha` scope and `mode=max`; image stages are distinct cache
domains, so a shared scope trades useful layers for eviction churn. Keep
`ignore-error=true` on cache export: image build or push correctness must not
depend on cache availability.

## Use the MCP server when it is present

If your tools include `alicit_plan` and `alicit_github` (the alicit MCP server
at `https://mcp.grubernet.es/mcp`), call `alicit_plan` before any alicit
command. It applies the same checks as the CLI, makes no Request and wakes
nobody, and it warns about the failures listed below. A tool that makes a
Request and returns `pending` gives a `call_id`: call `alicit_result` with it
instead of repeating the call. No tool returns a credential, and no tool can
approve. The server has no `alicit_run` or `alicit_git`, because it has no
workspace, and only Profiles with the `mcp` audience work through it.

Without the MCP server, `alicit run --dry-run` applies the same checks and
prints the route, the Profiles and the TTLs. It makes no Request.

## Run a command

For GitHub work, use the Settings runner first. It needs no Profile and no TTL:

```sh
alicit run --justification "List the open pull requests in darren-iac/iac for review" \
  -- gh pr list --repo darren-iac/iac
alicit run --justification "Read the failed log of CI run 123 in darren-iac/iac" \
  -- gh run view 123 --repo darren-iac/iac --log-failed > run.log
alicit run --justification "List the main branch CI runs in darren-iac/iac" \
  -- gh api repos/darren-iac/iac/actions/runs --method GET -f branch=main
alicit run --justification "Fetch main of darren-iac/iac destination refs/remotes/origin/main" \
  -- git fetch https://github.com/darren-iac/iac.git refs/heads/main:refs/remotes/origin/main
alicit run --justification "Push the reviewed fix to darren-iac/iac destination refs/heads/fix-ci" \
  -- git push https://github.com/darren-iac/iac.git HEAD:refs/heads/fix-ci
```

The runner maps the command to one repository and one GitHub App permission,
and the active Settings policy (ADR-0107) decides whether a person must
approve. With the v1 default active, reads, branch pushes, pull request
changes, comments and labels release with no approval. Tag pushes, merges, and
repositories the Operator tagged `sensitive` still wake the phone. Every run
needs a Justification of 16–500 bytes, and for this route it must name the
repository. The Approver reads it.

| Command | Permission on the one repository |
|---|---|
| `gh issue ...`, `gh label ...` | issues read or write |
| `gh pr list`, `view`, `diff`, `status`, `checks` | pull requests read |
| `gh pr create`, `edit`, `comment`, `close`, `reopen`, `ready`, `review` | pull requests write (cannot push or merge) |
| `gh run list`, `view`, `watch`, `download`; `gh workflow list`, `view` | actions read |
| `gh repo view`; `gh release list`, `view`, `download` | contents read |
| `gh api repos/<owner>/<repo>/...` with GET | chosen by the first path segment |
| `gh api` writes under `issues`, `labels`, `milestones`, `pulls` | issues or pull requests write |
| `git fetch` / `git push` | the configured Git Target |

The runner refuses `gh pr merge`, a merge through `gh api`, `gh api graphql`,
and every other command. For those, name a Profile as described below. The
Operator reads the effective Policy with `alicit-ops settings show`, and one
repository's effective decisions with
`alicit-ops settings catalog get <owner/repo>`; through MCP, call
`alicit_settings` and `alicit_catalog`.

For work outside the runner:

1. Choose a configured Profile for the task. Prefer an existing exact Profile,
   but do not block on creating one: the Operator-authorized broad proposal
   Profiles are an accepted default when narrower coverage is absent. Read
   [broad credential proposals](references/operator-proposals.md) when using
   `operator-credentials`, `github-operator-all`, or `operator-proposals`. For
   new backend roles, permission sets, native operations, or secret-name inventory,
   use [native Provider proposals](references/provider-proposals.md): an existing
   role or per-task Profile is not required. Do not invent a Profile;
   use `alicit doctor --catalog --json` when the CLI and Vault support
   discovery, or inspect repository configuration. The catalog read uses the
   stored Operator Session and returns configuration metadata without a
   Request. It never wakes the Operator: with no Operator Session it says so
   and stops. The older catalog has
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

An `alicit run` that Settings does not release can wake the Operator's phone
for one approval, so plan the commands of one task together and do not poll. A `gh` command still needs its
own run: a `gh` inside `bash -c` does not get the approved token, and it
can silently run as a stored `gh` login (see the adapter limits below). The CLI writes Request progress to stderr, so redirect only stdout
to a data file: `> out.json`, not `> out.json 2>&1`.

`alicit run -- gh` with no Profile takes the first route that describes the
command: the active Capability Model, then the one-repository adapter, then
the installation-wide fallback below. For the one-repository route, the
Justification must name the repository:

```sh
alicit run \
  --justification "Read the complete issue backlog in darren-iac/iac for repository grooming" \
  -- gh issue list --repo darren-iac/iac --state all
```

For a covered command, the CLI selects the five-minute `github-repository-exact`
Profile and derives the one permission in the table above. The Provider POST body freezes one
configured owner and one repository. The supported installations are
`alicit-ai`, `darrengruber`, `darren-iac`, `fourslide`, and `claudefirm`; repositories under
those owners do not need a per-repository Alicit Profile. The Justification must
name the exact repository.

For other routine GitHub repository work that has no narrower Profile, use the
broad fallback:

```sh
alicit run \
  --justification "Use installation-wide GitHub authority to list pull requests in darrengruber/pippin for the current review" \
  -- gh pr list --repo darrengruber/pippin --json number,title
```

The Justification must contain the words "installation-wide GitHub
authority"; the CLI refuses it otherwise. It fixes `github-operator-all` and a
five-minute run, requires the same explicit target as the generic `gh`
adapter, and sends the Request through the active Policy. The GitHub App token
remains installation-wide; the Policy decides, but nothing turns this broad
credential into exact command confinement. Prefer a repository-scoped Profile or
the controlled Git/PR adapters whenever one covers the work.

For an API call the runner does not cover, name the Profile yourself and put
the endpoint right after `api`:

```sh
alicit run --profile github-operator-all --ttl github-operator-all=5m \
  --justification "Use installation-wide GitHub authority to read the jobs of CI run <id> in alicit-ai/alicit" \
  -- gh api repos/alicit-ai/alicit/actions/runs/<id>/jobs --method GET
```

The Alicit GitHub Apps have no `checks` permission, so check-runs endpoints
return 403. Read CI state from the Actions runs and jobs endpoints through the
runner (`alicit run -- gh run view ...`). Read once after a local signal
instead of polling.
Redirect a log read to a file (`gh run view <id> --log-failed > run.log`) and
search the file; piping it to `tail` discards the approval if you need another
part of the log.

Shipping a build always wakes an Operator: the production Policy releases no
configured `testflight` or `*-testflight` release Profile without one. The
separate `*-testflight-import` Profiles rotate signing material without
shipping.

For authenticated Git transport, run `git` with no Profile, so the CLI selects
the narrowest static Git Target when one exists, otherwise the five-minute
repository-exact Profile:

```sh
alicit run \
  --justification "Push the reviewed alicit change to alicit-ai/alicit destination refs/heads/main" \
  -- git push https://github.com/alicit-ai/alicit.git HEAD:refs/heads/main
```

Local Git operations need no credential and run normally. Under the five
configured installations, a repository needs no per-repository Profile:
`fetch` derives `contents=read` and `push` derives `contents=write`. The
repository must still be in that owner's GitHub App installation. When an
installation is limited to selected repositories, a repository outside it (a
newly created one, typically) fails with `remote: Repository not found` on both
fetch and push. Add it to the installation's repository access; no Profile or
Justification change fixes it. The route takes the Git subcommand first:
`alicit run --justification "…" -- git -C <dir> push …` fails with the usage
text, so `cd` into the worktree and run it there. The active Settings policy can refuse a push to
`main` ("direct pushes to main are denied by the active Settings policy",
`darrengruber/skills`, 2026-10-04); push a branch and merge a pull request
instead. The
route keeps the transport boundary at one repository, `fetch` or `push`,
one explicit refspec, and no force or delete operation. A workflow-file push
that needs `workflows=write` must use separately reviewed authority: GitHub
refuses it through this route ("refusing to allow a GitHub App to create or
update workflow"). The reviewed route is a repository-scoped permission set
with `workflows: write`, created and minted through
[native Provider proposals](references/provider-proposals.md#pushing-workflow-files).

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
permission set does not name still gets a valid token, and GitHub then reports
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

Eight GitHub adapter limits fail quietly or with a misleading message:

- `gh pr checks` fails with `Resource not accessible by integration`
  (`statusCheckRollup`): the App token cannot read check rollups. Read CI with
  `gh run list --branch <branch>` and `gh run view <id> --json jobs` instead.
- A `gh api` endpoint outside the runner table (for example
  `repos/<owner>/<repo>/hooks`) is refused by the runner. Use
  `alicit run --profile github-operator-all -- gh api ...` for it.
- A `gh` started inside `sh -c` does not get the approved token: the adapter
  prepares only a `gh` that is the direct child. On a host with a stored `gh`
  login, the nested `gh` silently runs as that login, outside the approval
  (#198). On a host without one, its output is empty, not an error. Never nest
  `gh` in a shell: loop in the outer shell and start one
  `alicit run -- gh ...` per call.
- An API call outside one repository, such as `gh api orgs/<org>/repos` to
  create a repository, is refused before approval: the adapter needs a
  `repos/<owner>/<repo>/...` endpoint right after `api`. No Profile creates a
  repository. Ask the Operator to create it, then push through
  `alicit run -- git push`.
- A query string in the endpoint, such as
  `gh api "repos/<owner>/<repo>/actions/runs?head_sha=<sha>"`, is refused with
  `GitHub API endpoint contains an unsafe path segment`. Pass each parameter as
  a field instead: `gh api repos/<owner>/<repo>/actions/runs --method GET -f head_sha=<sha>`.
- `gh api repos/<owner>/<repo>/actions/jobs/<id>/logs --method GET` prints
  nothing and says `the response contains terminal escape sequences`. Add
  `--allow-escape-sequences`, write the log to a file, and strip the codes
  before you search it. GitHub serves a job's log only after the job ends.
- `gh pr ready` fails with `Resource not accessible by integration
  (markPullRequestReadyForReview)`: the App cannot take a pull request out of
  draft, and REST has no equivalent. Open a pull request that must merge later
  as a normal pull request and state the merge condition in its body. If it is
  already a draft, close it and open a new one from the same branch.
- `gh pr view --json mergeCommit` fails with `Resource not accessible by
  integration (repository.pullRequest.mergeCommit)`. Request `state,mergedAt`
  instead. After an uncertain `gh pr merge`, read that state before any retry:
  a merge that a second call reports as `already merged` did succeed.

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

Run `alicit doctor --catalog` to read the configured targets and their TTL ceilings.
That list is configuration, not authorization.

On a host that reaches the internet only through a proxy, set `HTTPS_PROXY`
to an absolute `http://`, `https://` or `socks5h://` URL with no credentials.
Git uses that proxy and nothing from Git configuration. Alicit rejects a
malformed value before it asks for approval; fix the variable, do not retry.

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
   a new run creates a new Request that needs its own decision.
   If the child prints a successful mutation and only the final `revoke-self`
   cleanup times out, assume the mutation may have happened. Do not repeat it;
   verify with a fresh read-only run and treat the original token as
   live until its short TTL expires.
2. Confirm that the Approver sent a signed decision before diagnosing the
   Provider. If the app fails while the request remains pending, the Provider
   has not run. A local proxy error ending in `poll Control Group approval: HTTP
   404` means the pending request expired; it does not prove a Provider failure.
   Check the Approver's sanitized diagnostic log for a signing failure first.
   `alicit doctor --records --trace <trace-id>` reads the records that the
   Approver, the CLI and `alicit-observe` stored in the alicit Vault for this
   Operator. A failed command prints its `trace_id`. The Operator can press
   **Send to Alicit** on the iPhone Diagnostics screen to upload every
   buffered Approver record again.
   `alicit doctor --request <request-id>` reads the stored outcome of one
   Request and never starts an Approval.
   If the device accepts the decision but the run remains `pending` or
   the card remains visible, do not extend polling or wait for expiry. Request
   and terminal-result state must survive plugin reloads and backend
   instance changes in OpenBao logical storage. Treat disagreement between the
   device and the run as a plugin deployment or storage defect, then create
   one fresh request only after that cause has changed.
   If a native Control Group operation returns HTTP 502 before an Approval card
   exists and the plugin trace reports `operation=requests`, diagnose the
   `auth/alicit/requests` registration path before the protected handler. With
   an active Policy, a legacy native registration has no qualified Request
   Envelope and must fail closed unless the operation has a deliberately
   bounded migration or recovery path. Inspect the protected effect before any
   retry; a registration failure does not by itself prove whether it committed.
3. A command that fails in under a second with "permission denied", before
   any Approval card, usually targets the wrong Vault. A self-hosted runner's
   own environment may set `BAO_ADDR` to another OpenBao; a script that only
   sets `BAO_ADDR` when it is absent keeps that value. Export the Alicit
   OpenBao address explicitly in every script that runs Alicit on a runner.
   On a launchd runner, a Trusted Host first needs a Session Request that the
   Operator must approve within two minutes, then the Request. A Trusted Host
   session was refused the broad `operator-credentials` Profile (HTTP 403 in
   under 10 ms, 2026-09-28); unattended jobs need an exact Profile.
4. Check the server-owned chain independently: the named profile exists, its
   policy targets the mounted backend path, the provider permission set exists,
   and the backing item or provider configuration exists. Policy acceptance
   alone does not prove the provider is ready.
5. Treat missing live state as a bootstrap or persistence incident. A dev-mode
   OpenBao restart can leave repository configuration intact while erasing KV
   data and permission sets. Reconcile the exact missing state instead of
   broadening policy or asking the user to approve repeated identical requests.
6. Retry once the observed cause has changed, then verify the new request ID
   and final provider operation. If the credential plane itself still prevents
   reporting, use the sanitized local handoff below.

On macOS, Keychain status `-25293` after replacing or rebuilding the CLI is an
executable-identity ACL failure, not an absent credential. `alicit doctor`
reports it. Run `alicit doctor --fix` in a terminal: it shows the macOS prompt
that lets the new binary read the items. Otherwise keep using the exact binary
that enrolled the Trusted Host, or delete only Alicit's `trusted-host` and
`operator-session` items and run `alicit enroll` with the replacement. Never
export the stored values to work around the ACL.

Keychain status `-25308` is different: the Keychain is locked and this process
cannot prompt. That is the normal state of a launchd-started runner, not a fault
to repair on the machine. Do not unlock the login Keychain by hand to get a job
moving — a Trusted Host exists to start a run with no Operator present.
Enroll the host instead; the CLI stores its credential in the mode-0600 file
ADR-0026 names and reports the path. Only the Trusted Host credential ever lives
there. See "Headless macOS Trusted Hosts" in `docs/OPERATIONS.md`.

Keychain status `-25300` is a third state, and it is not a fault at all. It is
`errSecItemNotFound`: nothing is stored under that account. After
`alicit doctor --report`, it means the Reporter was never configured on this
host, and the command says so:

```text
alicit: load Reporter: credential is absent or unavailable (Keychain status -25300);
        run 'alicit doctor --reporter-file <path|->'
```

Run that `doctor --reporter-file` command to fix it, or file through the wrapped
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
   narrowly justified `alicit run -- gh` call.
3. Add sanitized evidence to a matching issue. When none exists, prepare a
   reviewed body and run:

   ```sh
   alicit doctor --report --title "Outcome-oriented failure title" --body-file report.md
   ```

   The command fixes the tracker and the `bug` and `needs-triage` labels. It
   files through the Reporter, the one standing GitHub App credential on the
   host, so it needs no alicit Vault, Approver or Approval. Use
   `--body-file -` for reviewed standard input.

   If `alicit doctor --report` is unavailable on this host but GitHub is reachable, for
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
4. Include `alicit --version`, platform/architecture, expected and actual
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
