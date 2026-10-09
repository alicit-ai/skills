# Broad credential proposals

The Operator explicitly authorized broad proposals to increase velocity on
2026-09-13. Prefer existing exact Profiles when convenient; absent one, use these
configured broad Profiles instead of creating another per-task Profile.
Confirm their presence in live discovery first. Source configuration alone is
not a deployed grant. Each credential read still requires an Alicit Approval.

- `github-operator-all`: the existing `gh` adapter uses the target owner's
  `operator-all` permission set. The token inherits all repositories and
  permissions already granted to that GitHub App installation. State this broad
  authority in the Justification; do not describe it as a single-repository token.
- `operator-credentials`: read stored KV credential sets and credential outputs
  from the configured GitHub, AWS and Cloudflare Providers. Existing native role
  names and known KV paths can be requested without individual Profiles.

Both default to one hour and allow fifteen minutes for the Request decision.
The Invocation lifetime does not shorten a returned static secret or necessarily
match the Provider credential lifetime. Keep credentials in the consumer process;
never print, persist, or extract Provider configuration/seed credentials.

## GitHub commands

The normal broad route is `alicit run -- gh` with no Profile. It runs for
five minutes, still requires an explicit target, and the Justification must
name the installation-wide authority:

```sh
alicit run \
  --justification "Use installation-wide GitHub authority to publish the reviewed Pippin migration in darrengruber/pippin" \
  -- gh pr create --repo darrengruber/pippin --head feat/shared-apple-release \
     --base main --title "Use the shared Apple release runner" --body-file pr.md
```

Use the equivalent long form when a different TTL is genuinely
needed:

```sh
alicit run --profile github-operator-all \
  --justification "Use the installation-wide GitHub token to publish the reviewed Pippin migration in darrengruber/pippin" \
  -- gh pr create --repo darrengruber/pippin --head feat/shared-apple-release \
     --base main --title "Use the shared Apple release runner" --body-file pr.md
```

The controlled Git/PR adapters retain their own operation limits. This generic
GitHub token is broader authority; it is not proof that subsequent actions stay
within the Justification. The active Policy evaluates the Request and the
route remains broad. The Policy releases no configured TestFlight release
Profile without an Operator, so shipping a build always wakes one.
Use a reviewed consumer for several API operations
within one approved credential session rather than requesting a new token for
every API call. Do not reuse the credential of a completed run elsewhere.

`alicit run -- git` with no Profile is the narrower authenticated transport case:

```sh
alicit run \
  --justification "Push the reviewed alicit change to alicit-ai/alicit destination refs/heads/main" \
  -- git push https://github.com/alicit-ai/alicit.git HEAD:refs/heads/main
```

It derives the exact Profile from the configured Git Target and caps the TTL at
five minutes. The controlled transport still accepts only `fetch` or `push`
with one explicit refspec; local credential-free Git operations run normally.

## Stored sets and other Providers

Create a non-secret request file identifying the endpoint and JSON field paths:

```json
{"path":"kv/data/my-app/credentials","env":{"SERVICE_TOKEN":["data","data","token"]}}
```

This helper takes exactly `path` and `env`, with the mount inside `path`
(`cloudflare/creds/<role>`). `provider-proposal.py` takes a different form,
`{"mount", "path", "method", ...}`; giving that form to this helper fails before
any Request.

Replace that example with a known stored set and its actual field names. Then:

```sh
alicit run --profile operator-credentials \
  --justification "Read the existing my-app credential set for the reviewed deployment task" \
  -- python3 scripts/with-proposed-credentials.py request.json -- ./deployment-consumer
```

The helper reads the proposal before the Request, refuses redirects, and maps selected
string fields directly into the child environment. It removes the proxy capability
and ambient GitHub/AWS authority. The child must not print credential values.
For AWS dynamic credentials select `data.access_key`, `data.secret_key` and
`data.security_token` with the corresponding AWS environment names. Supply the
region explicitly to the consumer.

For new roles, permission sets, arbitrary native Provider operations and secret-name inventory, use [native Provider proposals](provider-proposals.md). This credential-read route enables existing credential outputs. A missing Provider, native role,
secret, external permission or OAuth consent remains a concrete setup gap; a
broad Profile cannot create that missing authority. Full secret-name inventory
and arbitrary new Provider role construction are not supplied by this change.
