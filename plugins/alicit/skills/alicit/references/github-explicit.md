# Direct GitHub credential requests

Use this branch for generic GitHub credentials without a reusable Profile, after
[explicit-access rollout and discovery checks](explicit-access.md). Production
capability issuance and Apple v5 delivery are still pending. The locally
qualified Provider is `vault-plugin-secrets-github` v2.3.2. The existing controlled
Git/PR adapters remain a separate route; do not claim their branch or operation
limits apply to a generic token consumed by another program.

Choose a published capability for POST `/v1/<configured-github-mount>/token` with
required `installation_id`, `repository_ids` and `permissions` parameters. These
selectors must all be server-owned finite choices. Do not invent production IDs,
omit a selector to get a default, or substitute a mutable permission-set route
while claiming its frozen scope is identical.

The qualified single-permission request uses string parameters such as:

```json
{"installation_id":"7","permissions":"contents=read","repository_ids":"42"}
```

Those numbers belong only to the disposable fixture. The plugin converts the
repository string to integer IDs and `contents=read` to a permission map. A
comma-separated permissions string is not a multi-entry map. Multiple permission
entries are not qualified through this finite-string interface yet.

Encode those exact body bytes as base64 in the explicit request's `operation.body`.
Use [the batch consumer command](batches.md) to receive the Provider response
without printing credentials into the Agent transcript. A consumer must check
the response's installation ID, repository IDs, granted permissions and
`expires_at` before using the token. Treat missing or mismatched metadata as an
unverified result, not permission to broaden or automatically repeat issuance.

An installation token can read every ref/content operation permitted by its
repository permissions; a generic token is not restricted to the task described
in the Justification. GitHub documents a one-hour token lifetime. Invocation TTL
and the returned OpenBao lease duration are separate limits. The Compose trial
observes this plugin's token revocation on Invocation cleanup against its API
fixture; production revocation still needs an actual end-user trial.

For reproducible local qualification, the repository's
`scripts/fixtures/run-github-explicit-compose.sh` runs one read request and a
consumer that prints only checked non-secret metadata. It is a fixture, not a
production adapter. Full `scripts/test-compose.sh` checks its complete path.
