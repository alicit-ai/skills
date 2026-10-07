# Issue tracker: GitHub

This repository uses [GitHub Issues](https://github.com/alicit-ai/alicit/issues)
for bugs, feature requests, specs, and agent-reported friction. Use `gh` only
through an Alicit invocation. The `github-issues` profile maps to the server-owned
GitHub permission set `issues`; Alicit retrieves its dynamic token through the
approved owner-scoped provider request and isolates `gh` from ambient tokens and
stored login configuration. Every non-API command must provide
`--repo alicit-ai/alicit`; owner-scoped `gh api` endpoints carry the same
target information in their path.

## Conventions

- **Create an issue**:
  For a bug, use `alicit doctor --report --title "..." --body-file report.md`. It fixes
  the repository and the `bug` plus `needs-triage` labels. It files through the
  Reporter, the one standing GitHub App credential on the host, so it needs no
  alicit Vault, Approver or Approval. Use `--body-file -` for reviewed standard
  input. For non-bug issues, use
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Create one triaged issue in alicit-ai/alicit for the scoped request" -- gh issue create --repo alicit-ai/alicit --title "..." --body-file ...`.
- **Read an issue**:
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Read issue 42 and its labels in alicit-ai/alicit to evaluate the matching report" -- gh issue view 42 --repo alicit-ai/alicit --json number,title,body,labels,comments`.
- **List issues**:
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Search the open and closed issues of alicit-ai/alicit for a duplicate of the reproduced failure" -- gh issue list --repo alicit-ai/alicit --state all --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`.
  Add appropriate `--label` and `--state` filters.
- **Comment on an issue**:
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Add sanitized reproduction evidence to issue 42 in alicit-ai/alicit" -- gh issue comment 42 --repo alicit-ai/alicit --body "..."`.
- **Apply or remove labels**:
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Mark issue 42 in alicit-ai/alicit ready for an implementation agent after verifying its scope" -- gh issue edit 42 --repo alicit-ai/alicit --add-label ready-for-agent`.
  Use `--remove-label` for removal.
- **Close an issue**:
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Close resolved issue 42 in alicit-ai/alicit with the verified outcome" -- gh issue close 42 --repo alicit-ai/alicit --comment "..."`.

Pass `--repo alicit-ai/alicit` explicitly so neither the target nor the
approval justification depends on the current directory.

Every command above targets `alicit-ai/alicit`, which is the one repository
the `issues` permission set names. For issue and label work on any repository
under the five configured owners (`alicit-ai`, `darrengruber`, `darren-iac`,
`fourslide`, `claudefirm`), run `gh` with no Profile:
`alicit run --justification "..." -- gh issue list --repo <owner>/<repo>`, with
a Justification that names `<owner>/<repo>`. It
selects the five-minute `github-repository-exact` Profile and derives
`issues=read` or `issues=write`. A static Profile such as
`github-renegade-agent-issues` for `darrengruber/renegade-agent` also works for
its one repository. A Profile used against a repository its permission set does
not name still gets a valid token, and GitHub then reports
`Could not resolve to a Repository`.

A `gh api` command must name its method with `--method` whenever it passes
`-f`, `-F`, `--field`, `--raw-field` or `--input`. Those flags make `gh` send a
POST, and Alicit rejects the command rather than approve a write that reads
like a read. The wayfinding commands below already do this.

## Pull requests as a triage surface

**PRs as a request surface: no.** If this changes, define a narrow server-owned
GitHub permission set for PR operations and use the corresponding
`github-<permission-set>` profile for the wrapped `gh pr` commands. GitHub shares
one number space across issues and PRs; when a bare `#42` is ambiguous, resolve
its type without mutating it before taking a write action.

## Publishing and fetching

When an engineering skill says **publish to the issue tracker**, create one
GitHub issue using the wrapped create convention above. When it says **fetch the
relevant ticket**, use the wrapped read convention above with comments and
labels included.

## Report quality and safety

Before filing, search open and closed issues for the same symptom and root cause.
Prefer adding sanitized reproduction evidence to an existing issue over creating
a duplicate.

New issues should include:

- a short outcome-oriented title;
- the expected and actual behavior;
- the smallest safe reproduction or command shape;
- `alicit --version`, platform, and architecture;
- the requested profile names and TTLs;
- the exact non-secret justification shown for approval;
- relevant sanitized error text and logs; and
- any attempted workaround and whether it changed the result.

Never include credentials, bearer tokens, device or polling secrets, enrollment
codes, private URLs with embedded credentials, secret values, or unreviewed
command output. Replace sensitive values with explicit placeholders and say what
was redacted.

Agents file bug reports with `alicit doctor --report`. It sends one fixed issue-create
request for this repository through the Reporter, and it works when the alicit
Vault or every Approver is unavailable. Search for duplicates through a
separately justified read before creating the report.

If `alicit doctor --report` itself is unavailable but GitHub is reachable, use the
wrapped `gh issue create` convention above with the `bug` and `needs-triage`
labels. That route goes through the alicit Vault and an Approval, so it
bypasses nothing. Keychain status `-25300` from `alicit doctor --report` is the common cause: it
means the Reporter is not configured on this host, not that the Keychain is
broken.

If Alicit itself prevents GitHub authentication, do not
bypass it or recurse into another Alicit invocation. Save the complete sanitized
issue body in the originating repository as
`bug-reports/YYYY-MM-DD-alicit-<short-slug>.md`, report its absolute path to the
user, and keep it until a maintainer records the resulting issue URL. This local
outbox is a durable handoff, not a claim that GitHub accepted the report. An
Alicit maintainer checking workspace reports should discover them with a file
inventory such as `rg --files <workspace-root> | rg '/bug-reports/[^/]+\.md$'`,
then perform the required duplicate search before filing each report.

Every new report starts with `needs-triage` unless a maintainer has already
confirmed its disposition.

## Wayfinding operations

For skills that use a map and child-ticket workflow:

- **Map**: one issue labelled `wayfinder:map`, with Notes,
  Decisions-so-far, and Fog sections. Create it through Alicit with a
  justification naming the map and repository.
- **Child ticket**: create an issue with the relevant `wayfinder:<type>` label
  (`research`, `prototype`, `grilling`, or `task`), then link it using
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Link issue CHILD as a sub-issue of MAP in alicit-ai/alicit" -- gh api repos/alicit-ai/alicit/issues/MAP/sub_issues --method POST -F sub_issue_id=CHILD_DATABASE_ID`.
  If sub-issues are unavailable, use a task list in the map and put
  `Part of #MAP` at the start of the child body.
- **Blocking**: use GitHub's native dependencies via
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Record BLOCKER as blocking CHILD in alicit-ai/alicit" -- gh api repos/alicit-ai/alicit/issues/CHILD/dependencies/blocked_by --method POST -F issue_id=BLOCKER_DATABASE_ID`.
  Fetch the database id with a separately justified wrapped
  `gh api repos/alicit-ai/alicit/issues/NUMBER --jq .id`. If dependencies
  are unavailable, use a `Blocked by: #NUMBER` line.
- **Frontier query**: list open children through the wrapped list convention,
  discard assigned tickets and those with open blockers, and take the first in
  map order.
- **Claim**: the first write is a separately justified
  `alicit run --profile github-issues --ttl github-issues=5m --justification "Assign issue NUMBER in alicit-ai/alicit to this agent for the scoped implementation" -- gh issue edit NUMBER --repo alicit-ai/alicit --add-assignee @me`.
- **Resolve**: use separately justified wrapped commands to comment with the
  answer, close the child, and append the durable context pointer to the map's
  Decisions-so-far.
