# Single explicit credential requests

Use this route only with an installed CLI supporting `--access-file`, a Vault
catalog reporting `explicit_requests: single_operation`, compatible active
Policy/native token authority, and an Approver that validates displayed Digest
v5. The catalog advertises protocol support, not an access grant. As of
2026-09-13 this path is qualified in disposable Compose only; production
capability issuance and Apple v5 delivery are pending. Do not replace the trusted
installed CLI or enable production authority merely to bypass that rollout.

Read `alicit doctor --catalog --json` through the existing bound Operator Session. Choose
one published capability matching the required Provider operation. Do not invent
a capability ID, path, method or parameter choice. Save a regular JSON file with
this shape (the names below belong to the Compose fixture only):

```json
{
  "capability_id": "fixture-read",
  "operation": {
    "path": "/v1/capability-fixture/credential",
    "method": "GET",
    "body": null
  },
  "ttl_seconds": 120
}
```

Then invoke a child that uses the mediated OpenBao proxy:

```sh
alicit run --access-file request.json \
  --justification 'Read the Compose fixture credential to verify the explicit access path' \
  -- bao read -format=json capability-fixture/credential
```

The file is frozen before authentication. `body` is base64-encoded exact JSON
bytes for POST/PUT string parameters; GET takes no body. Only published finite
non-secret choices are supported. Omit the TTL or set zero for the capability
default. Do not mix this flag with Profiles, Profile TTL overrides, or controlled
Git/PR inputs. The generic `gh` credential adapter still requires its Profile.

One explicit run can make one Request. Its native ceiling is independent
of Cedar; Policy may deny or require signed review. Invocation TTL bounds that
Invocation and does not establish the expiration of a returned Provider
credential. Inspect the first operation's result before requesting another
credential after a consumed-Invocation error. Changed-operation errors require
a new matching ask; unavailable-capability errors require refreshed discovery
and configuration inspection. Unknown transport failures may have an uncertain
Provider outcome and must not trigger automatic replay.

For several credentials or a Provider without a command adapter, read the
[batch consumer workflow](batches.md). It releases successes individually and
reports every item; a later failure does not roll back earlier credentials.

For GitHub's direct installation-token endpoint, read the
[Provider-specific request contract](github-explicit.md) before choosing parameters
or interpreting scope and lifetime.
