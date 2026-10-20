# Read CI with repository-scoped Actions

`gh pr checks` needs `statusCheckRollup`, which the Alicit GitHub App token
cannot read. The direct CLI warns before any Sign-in or credential Request;
the planner reports the same warning. The warning does not stop execution or
change authority. A subsequent GitHub refusal is a check-rollup access limit,
not failed Approval or Provider readiness. Do not broaden credentials for it.

Read the PR identity and current head first. Each command below is its own
credentialed invocation on the same repository; replace its placeholders:

```sh
alicit run --justification "Read PR <number> identity and head in <owner>/<repo> for CI qualification" \
  -- gh api repos/<owner>/<repo>/pulls/<number> --method GET
```

Record `number`, `head.ref`, `head.sha` and `head.repo.full_name` from that
response. Find candidate Actions runs using the head branch, or explicitly
name the GET method when using REST query fields:

```sh
alicit run --justification "List CI runs in <owner>/<repo> for PR <number> at its current head" \
  -- gh run list --repo <owner>/<repo> --branch <head-ref> \
  --json databaseId,headSha,status,conclusion

alicit run --justification "Read CI run <id> in <owner>/<repo> for PR <number> qualification" \
  -- gh run view <id> --repo <owner>/<repo> --json headSha,status,conclusion,jobs

alicit run --justification "List CI runs in <owner>/<repo> at the current PR head for qualification" \
  -- gh api repos/<owner>/<repo>/actions/runs --method GET -f head_sha=<head-sha>
```

Compare **every returned** `headSha` (REST `head_sha`) with the PR's current
`head.sha` before using a result. A branch or SHA query is a candidate filter,
not evidence that the response belongs to that commit. If no returned run
matches, CI qualification is unknown. If the PR head moves, read its identity
again and qualify the new SHA. Fork branch names can collide; a branch-name
match alone is never enough.

These reads retain pull requests read or Actions read on one repository.
Actions results do **not** enumerate every non-Actions required check or prove
that branch protection has been satisfied. Treat missing required-check
evidence separately; do not infer merge readiness from successful Actions alone.
