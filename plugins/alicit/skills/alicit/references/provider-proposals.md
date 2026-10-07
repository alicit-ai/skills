# Native Provider proposals

Use `operator-proposals` when an Agent needs a new backend role, a new permission
set, a native credential operation, or secret-name inventory. Prefer an existing
role when it fits; an absent role is not a reason to stop. The Agent writes the
backend's native role definition and submits it through this route, then requests
credentials from that role. Both operations require their own Approval with a
15-minute window, within an hour-long Invocation. Batch related downstream work
under one returned credential instead of repeatedly minting it.

The configured ACL covers these secrets mounts: `aws` and the four
`aws-accounts/<account>` mounts, `cloudflare`, the five GitHub installations
(`github/<owner>`), `kv`, `k8s`, `onepassword`, `gcp`, `rustfs`, `omniroute`
and `gmail`. It does not cover the `cloudflare-zones/<zone>` mounts. It allows
approved create/read/update/delete/list operations within the covered mounts,
but never their `config` paths. The helper is backend-independent: it validates
the mount against live discovery, rather than maintaining a backend type list.
A newly mounted Provider needs its mount added to the generated server policy
before the same helper can operate it. The coverage test catches omissions.

Provider `config` endpoints and Vault system/auth/identity administration remain
separate bootstrap authority. A proposal can define new AWS policy documents or
GitHub/Cloudflare permission sets; actual issuance still depends on the upstream
permissions held by the configured Provider. Return the observed upstream denial
to the Agent if those permissions are missing. Do not confuse writing a role with
successful credential issuance, or a Provider role with a new upstream IAM role.

## Which Vault a mount belongs to

The route reaches only the alicit Vault's mounts. The Cluster Vault, the
OpenBao that CI jobs and ESO read (`secret/ci/*`, `cloudflare-account/*`), is a
separate server, and its `secret` mount is not mirrored (the pending row in
`docs/providers/cluster-vault-parity.md`). A CI credential therefore has no
proposal write route: use that repository's own import workflow. A secret value
never goes in a proposal body in any case, because the helper puts the frozen
body in the process arguments.

Check a mount before you ask for anything. The helper refuses an undiscovered
mount locally, before any Approval:

```sh
python3 - <<'PY'
import importlib.util, json, subprocess
spec = importlib.util.spec_from_file_location("pp", "<skill>/scripts/provider-proposal.py")
pp = importlib.util.module_from_spec(spec); spec.loader.exec_module(pp)
mounts = [p["path"] for p in json.loads(subprocess.check_output(["alicit", "discover", "--json"]))["providers"]]
pp.validate({"mount": "secret", "path": "metadata/ci", "method": "LIST", "output": "keys"}, mounts)
PY
```

`ValueError: select a discovered secrets backend` means no proposal can reach it.

## Submit

Write a non-secret JSON proposal, for example an AWS role with the exact native
`credential_type`, `role_arns` and/or `policy_document` needed by the task:

```json
{
  "mount": "aws",
  "path": "roles/agent-task-name",
  "method": "POST",
  "body": {
    "credential_type": "assumed_role",
    "role_arns": ["arn:aws:iam::ACCOUNT:role/EXISTING_UPSTREAM_ROLE"],
    "policy_document": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":[\"arn:aws:s3:::BUCKET/PREFIX/*\"]}]}"
  }
}
```

Replace placeholders with actual task targets and review the native declaration.
Find the helper relative to the loaded skill directory, `scripts/provider-proposal.py`.
On brainiac it is installed at the path below and works from any repository:

```sh
python3 /Users/darren/.agents/skills/alicit/scripts/provider-proposal.py proposal.json \
  --justification "Create the AWS role for TASK with read access to BUCKET/PREFIX; use existing Provider authority"
```

The helper freezes the proposal in memory, adds its method/path and SHA256 to
the Justification, and invokes the enrolled `alicit` executable. The phone shows
that Justification and native operation. It does not render every arbitrary
backend field; the JSON artifact is the full reviewable declaration. This is the
existing native Control Group route, not new signed typed-operation enforcement.

The frozen, non-secret proposal travels as an encoded child-process argument;
the helper does not consume caller stdin. A consumer after `--` inherits that
stdin unchanged, including pipes and terminal input. Proposal declarations must
therefore contain no secrets, just as Justifications and process arguments must
contain none. Editing the source JSON after submission does not change the frozen
operation. Consumer exit status is propagated; no proposal transport file is left
behind.

For credentials add `env` mapping names to response selectors and a consumer:

```json
{"mount":"aws","path":"sts/agent-task-name","method":"GET","env":{"AWS_ACCESS_KEY_ID":["data","access_key"],"AWS_SECRET_ACCESS_KEY":["data","secret_key"],"AWS_SESSION_TOKEN":["data","security_token"]}}
```

```sh
python3 /Users/darren/.agents/skills/alicit/scripts/provider-proposal.py credential.json \
  --justification "Use the approved task AWS role to read BUCKET/PREFIX" -- aws s3 ls s3://BUCKET/PREFIX/ --region us-east-1
```

For secret-name inventory, propose `{"mount":"kv","path":"metadata/PROJECT","method":"LIST","output":"keys"}`.
LIST can print key names. Other operations print only completion metadata;
credential fields go directly to the consumer environment. Never put secret
values in a proposal body, Justification, or logs.

A just-minted Cloudflare API token can fail for a few seconds with
`Authentication error [code: 10000]`. Wait about 20 seconds in the consumer
before its first Cloudflare call, or retry it there; retrying the proposal costs
another Approval.

## Cloudflare roles

A role on the `cloudflare` mount names Cloudflare permission groups against
account or zone resources. This one serves a Pages site and its zone's DNS:

```json
{"mount": "cloudflare", "path": "roles/pages-SITE", "method": "POST",
 "body": {"ttl": 900, "max_ttl": 1800, "policy_document": {"Statement": [
   {"Effect": "Allow", "Action": ["Zone Read", "DNS Read", "DNS Write"], "Resource": ["cloudflare:zone:ZONE_ID"]},
   {"Effect": "Allow", "Action": ["Pages Read", "Pages Write"], "Resource": ["cloudflare:account:self"]}]}}}
```

Request it with `{"mount": "cloudflare", "path": "creds/pages-SITE", "method": "GET", "env": {"CLOUDFLARE_API_TOKEN": ["data", "token_value"]}}`.
Put every step of the job (create, deploy, attach domains, change DNS) in one
consumer, so one Approval covers it, and make the consumer stop before any
live DNS change when an earlier step fails.

Creating a Pages project with a GitHub `source` fails with error `8000011`
("internal issue with your Cloudflare Pages Git installation") until the
account has been linked to the GitHub App through the dashboard's **Connect to
Git** flow. Installing the Cloudflare Workers and Pages app on GitHub alone does
not link it. Have the Operator create the project in the dashboard, then let the
consumer adopt it. Attaching a custom domain in the dashboard re-creates the
zone's CNAME with a new record ID, which breaks any `import` block that names
the old one.

## Outcomes

The helper sends each native operation once and never retries automatically.
An HTTP failure reports only its safe numeric status, not the Provider response
body or arbitrary error text. A failed proposal keeps that status and names the
status lookup; it does not replace the diagnostic with a generic failure.
Preserve the Request IDs printed by Alicit and use
`alicit doctor --request <request-id>`, with `--json` for a machine-readable
record, for passive observation when supported by the installed CLI. The lookup
names the kind, Request or Sign-in Request, and prints the Provider HTTP status when the
server retains one. Inspect outer and native IDs separately: outer Approval or
API success does not establish native credential issuance. An unavailable observation
remains unknown and requires correlated server evidence; do not create a new Request
just to obtain status.
An interrupted or unknown write must be checked before resubmitting. Native
Control Group unwrap is not an exactly-once write facility; repeated unwrap can
repeat a write. Use immutable task-specific role names, and KV CAS when applicable.
Use separate proposals for intentional deletion or changing shared roles, naming
that effect in the Justification. A completed role write is followed by a separate
credential Request and a concrete upstream operation to qualify the intended access.

## Reaching an endpoint the command adapter refuses

The generic `gh` credential adapter only accepts an owner-scoped
`repos/<owner>/<repository>/...` endpoint, and rejects anything else *before*
authenticating. An organisation-level call such as
`gh api orgs/<org>/actions/runner-groups` therefore fails with

```
alicit: GitHub API commands require an owner-scoped repos/<owner>/<repository>/... endpoint immediately after api
```

**That refusal is about the adapter's shape rule, not about authority.** Read it
as "wrong command", not "insufficient permission" — the same installation may
hold the org permission already. Widening a permission set to answer it is the
wrong repair, and the explicit single-operation route is no help either when
`alicit doctor --catalog --json` reports no published capabilities.

Use the credential form of a proposal to put the token in the consumer's
environment, then call the API directly:

```json
{ "mount": "github/<org>", "path": "token/<permission-set>", "method": "GET",
  "env": { "GITHUB_TOKEN": ["data", "token"] } }
```

```sh
python3 .../provider-proposal.py credential.json \
  --justification "Request <org> <permission-set> to add <repo> to the <group> runner group" \
  -- bash ./grant.sh
```

Write the consumer to do the whole task under the one credential — resolve ids,
mutate, then re-read to verify — rather than minting per call. Keep it to
read-only probes plus the single intended mutation, and print only what is
needed to prove the outcome; the token is in its environment and must not reach
logs.

Issuance still depends on the upstream permissions the configured installation
holds. If the App lacks the org permission the call returns an upstream denial,
which is the real "not authorised" signal — unlike the adapter refusal above.

## Pushing workflow files

The GitHub App refuses a Git push that touches `.github/workflows/` without the
`workflows` permission, and `alicit run -- git push` never requests it. When
the installation holds that permission, create a repository-scoped permission
set once:

```json
{ "mount": "github/<owner>", "path": "permissionset/<repo>-workflows", "method": "POST",
  "body": { "org_name": "<owner>", "repositories": ["<repo>"],
            "permissions": { "contents": "write", "workflows": "write", "metadata": "read" } } }
```

Then mint it (`"path": "token/<repo>-workflows"`, `"env": {"GITHUB_TOKEN":
["data", "token"]}`) and push one explicit refspec from a consumer script that
sets `GIT_ASKPASS` to a throwaway script printing `x-access-token` and
`$GITHUB_TOKEN`, with `-c credential.helper=`. The token never reaches argv or
logs. This worked for `darrengruber/njdmv-checker` on 2026-09-28. Name the
workflow change in each Justification; the set outlives the task.
