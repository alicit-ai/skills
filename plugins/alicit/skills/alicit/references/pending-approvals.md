# Pending Approvals

Use this workflow when a user-initiated command may need an Approval or when
that Request waits longer than the Agent tool can remain in the foreground.

## Submit and await one Request

1. Show the Operator the non-secret Justification before submitting the
   command, so they know which card may wait. Existing task authorization is
   sufficient to submit it; this announcement is not another permission step.
   For `provider-proposal.py`, include the method/path and proposal SHA256
   suffix computed from the validated, frozen declaration by that helper.
2. Start the command once. If its wait may exceed the tool's foreground limit,
   use the tool's persistent process/session handle and await that same process
   asynchronously. Keep stderr visible for Request progress and retain its
   Request id. A tool wait ending is not evidence that the command or Request
   ended: inspect the existing process and Request before taking another action.
3. Through MCP, a `pending` response has a `call_id`; wait with `alicit_result`
   for that id. The result call does not submit another Request. Through the
   CLI, `alicit doctor --request <request-id>` reads the retained outcome and
   never starts an Approval.

An asynchronously awaited user-initiated call remains that same authorized
call. Autonomous automation must use `alicit run --unattended`: it never wakes
the Operator and never starts Enrollment or a Sign-in Request. Exit 75 means a
person is needed; end that pass and wait for a later authorized run. Preserve
this distinction when choosing a process handle or scheduling a future pass.

## An unanswered or failed Request

A native proposal was observed ending with `Provider operation returned HTTP
502` while `alicit doctor --request` reported `Decision: not_recorded`. That
combination occurred for an unanswered Request; HTTP 502 alone does not prove
it was unanswered or that a Provider mutation failed.

Read the retained Request outcome first. If it confirms the Request ended
unanswered, tell the Operator and ask before submitting a new Request. A later
Approval cannot revive a terminal Request. Preserve request ids and report an
unknown outcome as unknown; verify any possibly committed mutation with a
fresh read before considering another write. Never automatically replay the
proposal, renew authority or silently send the same Approval again.
