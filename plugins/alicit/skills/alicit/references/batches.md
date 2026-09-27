# Request several explicit credentials

Use this branch when the task needs several credentials and the installed CLI
supports `alicit request --batch-file`. First follow [explicit-access rollout and
discovery requirements](explicit-access.md). The server still advertises
`explicit_requests: single_operation`; a compatible CLI composes separate
Invocations. Local batch qualification does not enable production capabilities
or deliver Apple v5. Do not replace the installed trusted CLI to bypass rollout.

Choose 1–16 published capabilities and write one regular JSON manifest (at most
512 KiB). Each item has a unique lowercase ID, one exact explicit request, and a
16–500 byte Justification covering that item's task and scope. No Profiles are
required or accepted. This example uses disposable Compose metadata:

```json
{
  "version": "alicit.batch/v1",
  "items": [
    {
      "id": "fixture",
      "request": {
        "capability_id": "fixture-read",
        "operation": {"path": "/v1/capability-fixture/credential", "method": "GET"},
        "ttl_seconds": 120
      },
      "justification": "Read the exact Compose value for the batch consumer fixture"
    }
  ]
}
```

Run a consumer that parses newline-delimited JSON from stdin:

```sh
alicit request --batch-file batch.json -- ./credential-consumer
```

The consumer receives `ALICIT_BATCH_FORMAT=alicit.batch-result/v1`. Records carry
`version`, `id`, `capability_id`, `outcome`, optional `failure_code`, `explanation`,
`http_status` and `mint_id`. Only nonempty successful responses add
`response_body_base64`, containing the exact Provider response. Decode it in the
consumer, validate the Provider response and use the credential there. An HTTP
204 success can contain no credential; an empty body omits this field. Do not use `cat`, tee the stream into a
log, or print decoded credentials into an Agent transcript. The consumer's
stdout/stderr are visible to the caller. Stdin is reserved for these records.

The CLI freezes the entire file before authentication, then attempts items in
order with separate native ceilings and decisions. Successes are released as
they arrive. It continues after individual failures and stops starting new items
when the consumer exits or the batch is canceled. No later failure rolls back an
earlier credential. Keep the consumer alive until it finishes using credentials;
Invocation Tokens are revoked when it exits, subject to their individual TTLs.
A slow batch can outlive an early item's Invocation TTL. Neither that TTL nor
cleanup proves expiration or revocation of every Provider credential.

Inspect all final `alicit: batch-result <JSON>` lines on stderr. These contain no
Provider payload and cover every manifest item, even if the consumer exits early.
`outcome` is `succeeded`, `failed`, `unknown` or `not_attempted`. `delivery: written`
confirms bytes entered the pipe, not that the consumer used them; `unknown` means
a partial write. `invocation_cleanup: failed` or `unknown` requires investigation.
An issuance failure can leave `outcome: not_attempted` and cleanup `unknown`:
no Mint was attempted, but token issuance was not conclusively observed.

A zero exit means all items succeeded and were written, the consumer exited zero,
and known cleanup succeeded. A nonzero exit does not mean no credentials were
released. Never replay the whole manifest merely because it failed. Review each
receipt and the consumer's actual work, investigate uncertain Mint/Provider
outcomes using their IDs, and make a new minimal ask only after the cause is
understood. Forced process termination may prevent receipts and cleanup; this
route does not provide durable batch resume.
