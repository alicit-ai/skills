# Verify a release or retry failed CI jobs

Use the checkout at the reviewed commit. Record the repository, full commit,
CI run ID and attempt, installation namespace, expected StatefulSet revision,
cluster ID and serving plugin SHA-256 from the reviewed release record.

## Verify the running mount

Run this for both `alicit` and `alicit-hosted`, using each installation's own
cluster ID and expected checksum. The namespace observer reads the active
OpenBao mount. The serving command returns the cluster ID, serving checksum and UTC observation time.
The watcher also checks the Job’s Raft health result against pod readiness times. A failed latest observation, stale
receipt, identity mismatch or checksum mismatch blocks promotion.

```sh
scripts/release-observe.py serving --namespace "$namespace" \
  --cluster-id "$cluster_id" --expected-sha256 "$plugin_sha256"
```

For a new build, retain the Settings receipt from the image workflow's job summary or log. Match the immutable image digest, serving checksum, active and
Invocation Settings digests, `github-read` rule, `read` action, `allow` effect
and zero additional Wakes before pinning the candidate.

## Retry and watch a failed attempt

Read the failed main push CI run in `alicit-ai/alicit`. Confirm the exact run
ID, prior attempt and reviewed full head commit. With the supported CLI and
Operator-activated `actions.rerun_failed` operation, submit one request.

```sh
alicit run --justification "Retry the failed CI jobs for reviewed $commit in alicit-ai/alicit" \
  -- gh run rerun "$run_id" --failed --repo alicit-ai/alicit \
     --attempt "$previous_attempt" --match-head-commit "$commit"
```

Follow the [pending Approval](pending-approvals.md) while it is live. On
refusal, report the reason. If the outcome is uncertain, read the original
run before considering another request. A successful response includes
`observed_attempt`. Record that value. GitHub schedules the failed jobs and
their dependents. GitHub accepts the retry by run ID. Alicit checks the prior
attempt immediately before the POST and checks the next attempt afterward.
Coordinate concurrent retries of the same run, including retries from GitHub.

```sh
scripts/release-observe.py watch --namespace "$namespace" --commit "$commit" \
  --run-id "$run_id" --attempt "$observed_attempt" --revision "$revision"
```

The watcher uses unattended reads. It resumes after temporary redirects with
the same run, attempt and target revision. Its result records the Kubernetes
jobs and their source attempt, three Ready and updated voters on the requested
revision, and the final partition of three. On timeout or denial, keep the
last evidence and report the outstanding condition.
