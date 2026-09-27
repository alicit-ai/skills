# Controlled PR workflow

Use this route only after the compatible Vault, trusted CLI and processed
Internal TestFlight build are delivered. Source support and local fixtures are
not production readiness. Do not replace or re-sign the installed CLI to try it.

The controlled adapter supports `gh pr create`, `view` and `merge` for
`alicit-ai/alicit`. Always supply `--repo alicit-ai/alicit`, exactly one
matching Profile, and a Justification naming the action and repository. The
adapter sends one reviewed API operation itself; it never starts `gh`.

| Action | Profile | Required inputs |
|---|---|---|
| `pr create` | `github-alicit-pr-create` | `--head`, `--base`, `--title`, and exactly one `--body` or `--body-file`; optional `--draft` |
| `pr view` | `github-alicit-pr-read` | Explicit numeric PR number; selected JSON output is automatic |
| `pr merge` | `github-alicit-pr-merge` | Explicit numeric PR number, full lowercase `--match-head-commit`, one `--merge`, `--squash` or `--rebase` |

Each action runs through `alicit run` with its one Profile. Pass multiline text
with `--body-file`:

```sh
alicit run --profile github-alicit-pr-create --ttl github-alicit-pr-create=5m \
  --justification "Create one PR in alicit-ai/alicit from <branch> into main to <purpose>" \
  -- gh pr create --repo alicit-ai/alicit --head <branch> --base main \
     --title "<conventional title>" --body-file body.md

alicit run --profile github-alicit-pr-read --ttl github-alicit-pr-read=5m \
  --justification "View PR <n> in alicit-ai/alicit to <purpose>" \
  -- gh pr view <n> --repo alicit-ai/alicit

alicit run --profile github-alicit-pr-merge --ttl github-alicit-pr-merge=5m \
  --justification "Squash-merge PR <n> in alicit-ai/alicit at head <sha7> to <purpose>" \
  -- gh pr merge <n> --repo alicit-ai/alicit --squash \
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
Closing a PR is outside this adapter; use `alicit github` with an
installation-wide justification.

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
is not permission to repeat the mutation. A Mint success alone does not prove
that the PR operation succeeded. Generic credentials from other configured
Profiles can intentionally have broader authority.
