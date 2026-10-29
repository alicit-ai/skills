# Commit signing and Approved Merges

Use these commands after the compatible Vault, qualified CLI, Tenant Signing
Authority, active Policy and repository trust/checks are delivered. Read the
repository's activation evidence before treating source support as active.
Use the stable CLI promotion procedure; preserve the installed trusted binary
until a qualified release replaces it.

```sh
alicit run --justification "Sign the reviewed implementation commit" -- \
  git commit -m 'feat: add the feature'

alicit run --justification "Merge reviewed PR <n> in <owner/repo> at head <sha7>" -- \
  git merge --repo <owner/repo> --pull-request <n> \
    --match-head-commit <full-head-sha> --subject 'feat: add the feature' \
    --body-file merge-body.md
```

These routes use no Profile or TTL override. The CLI discovers one current
request-capable Tenant Membership; with several, select the intended Tenant
with `ALICIT_SIGNING_TENANT`. That selector grants no access.

Under the qualified signing Policy, ordinary commit issuance does not wake an
Approver. The Operator can narrow that Policy to require review or refuse.
It obtains a short-lived certificate and keeps the private key in
memory for one signature. The Operator becomes the committer; the author is
preserved. Certificate failure produces no commit. Background work adds
`--unattended` and ends the pass on exit 75; it never falls back to unsigned
commits or broader credentials.

An Approved Merge reviews the exact repository, PR, head, base, tree and
Conventional subject. Supply an explicit regular body file, including an empty
file for an empty body. The `alicit-ai/alicit` repository always needs an
enrolled-key phone Approval. Another repository can use a Policy release only
with a current covering autonomous Host Grant. The command signs a one-parent
commit and pushes with the reviewed base as its lease. The checkout and index
remain unchanged.

After an uncertain push result, inspect the remote and retained
`refs/alicit/approved-merges/<commit>` before making another Request. A stale
head or base requires fresh review. A completed Request alone is not proof
that the commit landed. Read back the remote commit and required checks.

Once signing is enabled, use this merge command rather than `gh pr merge`.
Treat refusal as a deployment or authorization result; broad credentials are
not a signing fallback. The full native authority, offline verification,
rotation and rollback contract is in `docs/operations/commit-signing.md` in
the Alicit repository.
