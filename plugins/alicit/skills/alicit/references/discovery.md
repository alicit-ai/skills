# Discover configured Providers and requestable access

Run `alicit discover --json` with the installed trusted CLI. It uses the bound
Operator Session and does not Mint a credential. Initial Session creation can
still require its own approval if no usable Session exists.

Recognize the catalog's coverage before choosing an ask:

- `alicit.access/v1` exposes configured Profiles only.
- `alicit.access/v2` also exposes published explicit capabilities.
- `alicit.access/v3` also exposes configured Provider mounts, including mounts
  without published explicit capabilities. Its coverage is
  `configured_provider_mounts_profiles_and_capabilities`.

In v3, `providers` contains path, type, public mount accessor, optional running
plugin/KV versions and `capability_ids`. Empty capability IDs mean no published
explicit capability for that mount; a Profile may still provide access. Choose a
Profile or an existing published capability matching the actual task. Do not
invent a capability, infer a grant from a mount name, or broaden a request because
nothing suitable is published. `unmatched_capability_ids` identifies configured
capabilities without an observed Provider mount; investigate configuration before
attempting to use them.

`provider_visibility: vault_root_namespace` is the actual scope of this reader.
It does not prove Tenant Membership or isolation. Optional `role_inventory` reports native GitHub permission-set, AWS role or
Cloudflare role names. Only `status: complete` establishes the returned name list;
`unsupported`, `unavailable`, `limit_exceeded`, or an absent object mean coverage
is incomplete. An unavailable list may reflect an empty native list's HTTP 404,
missing LIST permissions or a failed endpoint; it is not proof of no roles.
Custom mount paths need a reviewed collection LIST permission. Role contents,
credential readiness and parity with another OpenBao installation are not
established. Choose an existing Profile or capability even when a native role
name is visible; ask for suitable configuration when none matches the task. Version fields are observed metadata, not approved binary identity
or a guarantee that the explicit request language supports that Provider.

The inventory is read on each request, but is not an atomic snapshot with Profile
and capability configuration. `observed_at` is not a promise about a later Mint.
If the Provider inventory source fails, the server reports discovery unavailable;
do not interpret it as an empty installation or retry credential issuance.

For `explicit_requests: single_operation`, follow
[explicit request requirements](explicit-access.md), including compatible Policy,
native authority and Apple v5 rollout. For several credentials use the
[batch consumer workflow](batches.md). Neither a successful catalog read nor a
published capability establishes returned Provider credential expiry or scope
beyond the independently validated request boundary.
