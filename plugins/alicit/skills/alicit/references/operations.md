# Find the right Alicit operation

Use this index to choose a surface. Start with the [installed CLI and release
checks](global-cli.md) when behavior depends on which release is running.
Use [discovery](discovery.md) for configured access and plan the exact
operation before execution. A plan or catalog entry does not grant authority.

| Agent CLI command | Use |
|---|---|
| `alicit help` | Find the supported commands on this installation. |
| `alicit doctor` | Check health, discover access, read Request evidence, or report friction. |
| `alicit enroll` | Enroll the local execution host. |
| `alicit run` | Plan or run an exact operation. Use the routes below to choose access. |

| When the Operator asks to… | Use |
|---|---|
| Check the installed CLI, Vault, Host, or Operator Session | `alicit help`, `alicit --version`, and `alicit doctor --json`. Start with the read-only report. `doctor --fix` may require interaction. |
| Enroll a Trusted Host | `alicit enroll` on the execution host. Use the Approver for Host invitations and pass single-use invitations on stdin. Read [Trusted Hosts](https://github.com/alicit-ai/alicit/blob/main/docs/OPERATIONS.md#trusted-hosts-and-operator-imports). |
| Find configured Profiles, Providers, Capabilities or Git Targets without a Wake | `alicit doctor --catalog --json`. Read [discovery](discovery.md) for coverage and session requirements. |
| File or triage an issue, inspect CI, or check a release | Use the [GitHub runner](github-runner.md) and [issue tracker](issue-tracker.md). Tie CI evidence to the reviewed commit and read back any mutation. |
| Commit, fetch, push, create or merge a PR | Read [commit signing](commit-signing.md) and [pull requests](pull-requests.md). Git uses the local workspace and an explicit destination ref. Choose the merge route using live signing state. |
| Run AWS, Bao/Vault, or Kubernetes work | Use [command-derived access](command-access.md). For pod exec, one-off Approval, time-limited rules, or standing access, use [Kubernetes exec overrides](kubernetes-exec.md). |
| Choose an exact Profile, request explicit access, or run a multi-credential consumer | Use [discovery](discovery.md), [explicit access](explicit-access.md), or [batches](batches.md) as appropriate. Use [Provider proposals](provider-proposals.md) for reviewed native operations. |
| Diagnose or resume a pending Request | Use [pending Approvals](pending-approvals.md), `alicit doctor --request <request-id>`, and `alicit doctor --records --trace <trace-id>`. Verify the operation's effect before any retry. |
| Report Alicit friction | Use `alicit doctor --report` or follow “Report Alicit friction” in the main skill. |
| Promote a stable CLI or check marketplace delivery | Read [global CLI use](global-cli.md). Check the release, the installed binary, and the installed skill independently. |

## Operator operations

Check `alicit-ops help` for exact flags. Use the qualified checkout and the
[build and session procedure](https://github.com/alicit-ai/alicit/blob/main/docs/OPERATIONS.md#trusted-hosts-and-operator-imports).
This binary is separate from the distributed agent CLI. An expired session
can require a Sign-in Request. Prepare the change and show the reviewed target
before any signed activation.

| Command family | Use |
|---|---|
| `alicit-ops settings` | Read effective Settings, inspect or edit a draft, and request signed activation. See [Settings policy](https://github.com/alicit-ai/alicit/blob/main/docs/OPERATIONS.md#settings-policy-adr-0107) and [exec overrides](kubernetes-exec.md). |
| `alicit-ops policy` | Test or digest Cedar locally and request activation of a reviewed Policy revision. See [Cedar activation](https://github.com/alicit-ai/alicit/blob/main/docs/OPERATIONS.md#web-cedar-activation-adr-0132). |
| `alicit-ops capabilities` | Read, digest, and activate a reviewed Capability Model. Discover live coverage before planning execution. |
| `alicit-ops tenants` | Inspect Tenant Membership and Provider visibility. Use the reviewed Operator flow for changes. |
| `alicit-ops signing` | Manage or verify the Signing Record using the [TestFlight runbook](https://github.com/alicit-ai/alicit/blob/main/docs/OPERATIONS.md#testflight-release). |
| `alicit-ops testflight` | Release, assign a processed build, or work with TestFlight feedback. Use the [TestFlight runbook](https://github.com/alicit-ai/alicit/blob/main/docs/OPERATIONS.md#testflight-release) to distinguish a retry from assignment-only recovery. |

Host invitations and Allowances live in the iPhone and Android Approvers.
Use the Approver for signed decisions and History revocation of a live Invocation.

## Remote MCP

The gateway exposes the following prefixed tools. The remote server has no
local workspace and returns no credentials. Use the execution host for local
Git, native commands, and Operator writes. Check the tool schema and deployed
version before using a source feature.

| Tool | Use |
|---|---|
| `alicit_plan` | Plan a proposed run with no Request or Wake. Complete the local checks if the plan says the execution host is required. |
| `alicit_discover` | Read configured access. This can start a Sign-in Request if the remote session is missing. Use local catalog discovery for a strict no-Wake task. |
| `alicit_github` | Run one covered GitHub command with remote-supported authority. Use the local reviewed merge route for merges. |
| `alicit_result` | Resume a pending call by `call_id`. Keep polling the same call rather than submitting another operation. |
| `alicit_cancel` | Cancel a call by `call_id`. Read back any possible effect if the command had already started. |
| `alicit_request` | Read a retained Request by `request_id` without starting authentication or an Approval. |
| `alicit_diagnostics` | Read sanitized diagnostics, optionally by `trace_id`. |
| `alicit_settings` | Read active Settings, including signed overrides when the server exposes them. A missing session can start a Sign-in Request. |
| `alicit_catalog` | Inspect the Settings resource catalogue, including GitHub action decisions. It uses the remote Operator Session. For local access discovery without a Wake, use `alicit doctor --catalog` on the enrolled host. |
