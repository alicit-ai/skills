# Command-derived AWS and Bao/Vault access

This route requires compatible server, CLI and review-11 Approvers, configured
Providers and a separately provisioned issuer. Source support does not establish
that the installed service has enabled it. See the repository's
[implementation specification](https://github.com/alicit-ai/alicit/blob/main/docs/specs/command-scoped-access.md)
for configuration and qualification evidence.

Use the native command and a concrete justification without `--profile`,
`--access-file`, `--batch-file` or Profile TTL overrides on `alicit run`:

```sh
alicit run --justification "Read this application's configured SSM parameter" -- \
  aws --profile production ssm get-parameter --name /applications/example/config
alicit run --justification "Read this application's configured Bao database path" -- \
  bao kv get -mount=secret applications/example/database
```

The AWS `--profile` is a configured Provider selector, not a local credential
profile. Bao/Vault address and namespace selectors must identify a configured
destination. `ALICIT_VAULT_ADDR` selects the alicit control plane independently
of `BAO_ADDR`/`VAULT_ADDR`. Local credential helpers, endpoint overrides and
alternate credentials are isolated. Do not bypass a refusal through a shell
wrapper or a broader Profile.

Use the pure MCP planner, or `alicit run --dry-run`, before authentication.
Preflight reports Requested Access; the server resolves Credential Authority
and evaluates Policy. Unresolved mappings and unknown destinations fail before
native issuance. A missing permission requires a fresh request; never widen or
replay automatically.

Bao paths outside modeled KV routes require every effect category in Policy,
including paths named `creds` or `issue`. Endpoint names alone cannot establish
their effects. KV v2 mount configuration is deferred, and metadata mutation
authority includes destructive retention changes.

Review the native permissions, broader authority and lifetime. AWS defaults to
15 minutes and issued STS keys remain usable until their native expiry despite
Invocation cleanup or OpenBao lease revocation. Bao/Vault native tokens remain
behind a loopback proxy and are revoked on exit, with restart cleanup for
abandoned grants. Native credentials can be reused within their disclosed
authority; this feature does not confine a child to an exact command.

Wrangler support is researched and deferred. Follow the configured existing
Provider route for it rather than inventing command-derived coverage.

Kubernetes command access requires compatible review-12 delivery and explicit
signed activation; source support alone grants nothing. Use
`alicit run --justification "Read the owned canary ConfigMap in etcdrich" -- kubectl --context etcdrich -n alicit-kubectl-canary get configmap/canary`.
Context aliases and default namespaces are server owned. An optional alicit
`--duration` keeps runs at 600–3,600 whole seconds, default 600. Review and Policy
include another 60 seconds of JWT expiry tolerance and 10 seconds of successful
authentication caching in the native ceiling. Credentials use a token-free
kubeconfig and a memory broker; local kubeconfig authentication is isolated.
Tagged Hosts require explicit Kubernetes Host Grants. Never bypass a refusal
through a shell, Profile or another context. See the
[Kubernetes contract](https://github.com/alicit-ai/alicit/blob/main/docs/specs/kubectl-command-access.md)
for supported commands, frozen inputs and qualification gates.
