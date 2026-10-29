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

Inspect the same PR after an uncertain HTTP outcome or output failure before
creating another request. A successful PR operation followed by a cleanup error
is not permission to repeat the mutation. A Request success alone does not prove
that the PR operation succeeded. Generic credentials from other configured
Profiles can intentionally have broader authority.
