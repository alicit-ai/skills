# Controlled PR workflow

When commit signing is enabled, merge through
[Approved Merges](commit-signing.md). The Vault refuses the older `pr.merge`
routes below. Creation and viewing continue through their existing adapters.

Use this route only after the compatible Vault, trusted CLI and processed
Internal TestFlight build are delivered. Source support and local fixtures are
not production readiness. Do not replace or re-sign the installed CLI to try it.

The controlled adapter supports `gh pr create`, `view` and `merge`. Prefer
`alicit run` with no Profile when the deployed active Capability Model covers
the operation. Always supply `--repo <owner/repo>` and a Justification naming
the action and repository. The model's target reader determines the supported
repositories; the effective server policy determines whether approval is
required. A supported repository is not automatically an access grant.

### Choose draft status before creation

When you expect to mark your own draft ready, check the installed binaries and
the active Capability Model before passing `--draft`. The numeric PR below is
only an input to the local dry run. For an existing draft, use its real number.

```sh
alicit run --unattended --dry-run --json \
  --justification "Check draft support for the release PR in alicit-ai/alicit" \
  -- gh pr ready 1 --repo alicit-ai/alicit |
  jq -e 'any(.operations[]?; .capability == "pr.ready")'
alicit-ops capabilities show --json |
  jq -e '.found and any(.model.revision.models[]? | select(.provider == "github") |
    .operations[]?; .id == "pr.ready" and .transport == "server")'
```

If either check is unavailable and the work is ready for review, create the PR
ready. If a draft is required, agree who can mark it ready. Keep an existing
draft and its review history. After a transition, read the same PR back.

The legacy `github-alicit-pr-*` Profile route is restricted to
`alicit-ai/alicit`. Use exactly one matching configured Profile only when that
route is appropriate. Both controlled routes send one reviewed API operation
themselves; neither starts `gh`.

| Action | Legacy Alicit-only Profile | Required inputs |
|---|---|---|
| `pr create` | `github-alicit-pr-create` | `--head`, `--base`, `--title`, and exactly one `--body` or `--body-file`; optional `--draft` |
| `pr view` | `github-alicit-pr-read` | Explicit numeric PR number; selected JSON output is automatic |
| `pr merge` | `github-alicit-pr-merge` | Explicit numeric PR number, full lowercase `--match-head-commit`, one `--merge`, `--squash` or `--rebase` |

For the Capability Model route, omit Profile and TTL overrides. Pass multiline
text with `--body-file`:

```sh
alicit run \
  --justification "Create one PR in <owner/repo> from <branch> into main to <purpose>" \
  -- gh pr create --repo <owner/repo> --head <branch> --base main \
     --title "<conventional title>" --body-file body.md

alicit run \
  --justification "View PR <n> in <owner/repo> to <purpose>" \
  -- gh pr view <n> --repo <owner/repo>

alicit run \
  --justification "Squash-merge PR <n> in <owner/repo> at head <sha7> to <purpose>" \
  -- gh pr merge <n> --repo <owner/repo> --squash \
     --match-head-commit <full-sha> --subject "<title> (#<n>)" --body-file msg.md
```

## Prepare a PR for review

Use the shipped CLI and the active GitHub Capability Model for draft changes.
Specify the numeric PR and repository. Name the repository and intended change
in the Justification. Routine writes can proceed without a Wake when the
effective Settings, Host Grant and Policy permit them. An Approval identifies
the PR and the requested direction. For unattended work, exit 75 means the
operation needs a person and the pass ends.

```sh
alicit run --justification "List changed paths on PR 123 in owner/repo for review" \
  -- gh pr diff 123 --name-only --repo owner/repo

alicit run --justification "Mark PR 123 in owner/repo ready for review after verification" \
  -- gh pr ready 123 --repo owner/repo

alicit run --justification "Return PR 123 in owner/repo to draft while revising it" \
  -- gh pr ready 123 --undo --repo owner/repo
```

The file list uses repository-scoped PR read authority. GitHub's changed-files
endpoint caps the inventory at 3,000 files. The command reports when it cannot
verify a complete list and leaves standard output empty.

The alicit Vault performs the state transition and confirms the resulting
state on the same PR. An open PR already in the requested state succeeds
without a mutation. For an uncertain outcome, use a fresh PR read and check
its number, URL, open state and draft status before considering another
Invocation. If the CLI reports incompatible or inactive server support, check
the installed CLI and the Vault's active model. Older CLIs may still use the
legacy GitHub credential route for `gh pr ready`. The server-custodied route
requires the compatible CLI and active model together. If the effective policy
refuses the transition, inspect the Request outcome. Keep the original PR.

## Merge and recovery

A merge that reports `did not confirm success (HTTP 405)` did not merge. The
usual cause is a conflict with the current base; view the PR, fetch the base
and test the merge (`git merge-tree --write-tree origin/main <branch>`) before
any retry. The Git transport rejects force pushes, so push a rebased branch
under a new name and open a new PR. To keep the same PR, merge the base into
the branch and push that normally. Give the merge commit a Conventional subject
such as `chore: merge main into <topic>`: the release gate rejects Git's own
`Merge branch` subject, and a squash merge leaves the commit off `main`.
Closing a PR is outside this controlled adapter; use `alicit run -- gh pr close`
with an explicit `--repo` and repository-naming Justification through the
credential runner. Name installation-wide GitHub authority only when the
selected fallback actually requires it.

For merge or squash, also supply `--subject` and exactly one `--body` or
`--body-file` for the commit text. Rebase rejects those flags and preserves
existing commit messages. Use a regular body file for multiline text. It is read
before authentication and never reopened after approval. Empty bodies must be
explicit. Other flags, implicit PR selection, URLs, global options, auto-merge,
admin bypass and branch deletion are rejected before authentication.

Creation binds the stated live branch relationship; later branch commits can
change. Merge requires the exact head SHA, but follows the PR's current base
branch. It does not provide atomic base-ref enforcement. Check those semantics
and the full text in Details before approving.

For `alicit-ai/alicit` while release preparation is active, use `--squash`.
The deployed native release bridge requires a single-parent source; a legacy
two-parent merge cannot qualify automatic release reconciliation. If one has
already landed, inspect publication state, then roll forward with a reviewed
single-parent commit. Do not rewrite published history or restore the former
repository-write publisher to recover it.

Inspect the same PR after an uncertain HTTP outcome or output failure before
creating another request. A successful PR operation followed by a cleanup error
is not permission to repeat the mutation. A Request success alone does not prove
that the PR operation succeeded. Generic credentials from other configured
Profiles can intentionally have broader authority.
