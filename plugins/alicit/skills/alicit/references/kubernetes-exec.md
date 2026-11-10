# Kubernetes exec and signed Settings overrides

Choose the lifetime before preparing a change:

- **One request.** Run direct pod exec through the installed CLI with a
  concrete Justification. Use the normal Approval path for an interactive
  request. There is no Settings change to make for a one-off Approval.
- **A time window.** Prepare one signed Settings override with an explicit
  deadline. The editor and CLI suggest 24 hours for a newly authored rule.
  In a CLI draft, a positive `expires_at` is a UTC Unix timestamp in seconds.
- **Until revoked.** Set `"expires_at": 0` explicitly in a new CLI draft.
  This keeps the rule in effect until signed removal.

An override selects one enrolled Host ID or one server-owned Host Tag,
one cluster and namespace, and exact pod names. A replacement pod with the
same name remains in scope. Review shell authority in the named pod, including
its containers and live stdin. Host Grants, Provider ceilings, explicit
Settings restrictions, and Cedar still apply. A rule's lifetime governs future
issuance; each Invocation still has its own bounded lifetime.

## Run routine work without a Wake

1. Check that the installed CLI and Vault support the feature. On the actual
   execution host, use `alicit doctor --catalog --json` to inspect candidate
   `kubernetes_exec_overrides` when the server exposes them. Use the active
   Settings document to inspect the signed scope. A candidate alone does not
   authorize execution.
2. Plan the direct named pod command using [command-derived access](command-access.md).
   Use the local dry run for execution-host checks. Dry run makes no Request,
   does not read live resource discovery, and does not prove a rule will match.
3. When the Operator has asked for no Wake, add `--unattended`. For example,
   from the enrolled Host with an approved rule for this illustrative pod:

   ```sh
   alicit run --unattended \
     --justification "Check the application version in the approved development pod" -- \
     kubectl --context example-cluster -n dev exec -i app-dev -- sh -s < check-version.sh
   ```

   Use the reviewed context, namespace and pod. Pass live stdin to the direct
   command and keep Request progress on stderr. Exit 75 means this pass needs
   a person and woke nobody. Stop the pass and report the reason. A separate
   interactive run requires a user-initiated decision.
4. Verify the child result and the History observation `kubernetes_exec_release`
   for the expected override IDs, Settings revision, and bound scope. Use a
   disposable fixture for live qualification of new release behavior.

## Stage, sign and revoke

1. Confirm the feature is enabled in the deployed Vault. Read active Settings
   and the current draft. Resolve any unrelated draft changes with the Operator
   before editing. Prepare the reviewed Host, cluster, namespace, exact pod
   names and lifetime in web Settings or in a copy of the active document for
   `alicit-ops settings draft put <file>`. Keep existing rules. The Vault
   binds the cluster on draft save.
2. Read back the draft digest and reviewed scope. Use
   `alicit-ops settings activate --justification <reason>` to snapshot and
   review a new draft. `--digest` selects a previously stored revision.
   Match the activation Request digest to the reviewed draft and have the
   Operator sign that revision. Read back the active digest and scope.
3. Renew by editing the deadline in a draft and signing the change. For signed
   removal, use **Profile → Kubernetes overrides** on the Approver. Check
   the active rules, including overlapping rules that may still match. Expiry
   and removal affect future issuance. Revoke a live Invocation separately
   from History when needed.

Use the [operations runbook](https://github.com/alicit-ai/alicit/blob/main/docs/OPERATIONS.md#kubernetes-exec-overrides)
for deployment, disposable canary, and compatible rollback gates.
