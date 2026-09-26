# Unpublished dispatch plan cancellation v1

Owner: GridBridge. Additive HTTP contract, 2026-09-27. No MQTT cancellation or field stop.

`POST /api/v1/gridbridge/dispatch/schedule/{plan_id}/cancel` requires administrator authentication.
JSON: `requested_by`, `request_id` (the original creation identity), `plan_hash`, `reason`
(nonblank, at most 500 characters). Unknown fields are rejected.

Cancellation is permitted only for PLANNED with every target pending, attempts=0,
no publish error/timestamp and no Edge ACK evidence. No targets is also refused.
The original identity and hash must match. The plan row is locked in the same transaction
as cancellation, its reason/timestamp and the associated pending DR event cancellation.
The original payload/hash and target records remain unchanged.

Response is the existing plan envelope with mode=cancel, status=CANCELLED,
`cancellation={cancelled_at, reason}` and `idempotent_replay`.
Repeated identical cancellation returns the original result. Different reason or hash
returns 409; the original audit values are never overwritten.

Execute rejects CANCELLED (`PLAN_CANCELLED`) and DISPATCHING (`PLAN_DISPATCH_IN_PROGRESS`).
Before invoking any external publisher, execute commits a DISPATCHING reservation under
the plan and target VEN locks. Conflicting plans treat DISPATCHING as occupied. Completion
records EXECUTED/PARTIAL/FAILED. Only recorded FAILED/PARTIAL may use existing retry logic.
A process crash leaves DISPATCHING even if attempts rolled back: no automatic return to
PLANNED and no cancellation assuming non-delivery. Operator reconciliation is separate.

Cancellation errors: 404 PLAN_NOT_FOUND; 409 PLAN_IDENTITY_MISMATCH,
PLAN_HASH_MISMATCH, PLAN_NOT_CANCELLABLE, CANCEL_REQUEST_MISMATCH.
Published, partially published, failed-attempt or unknown delivery states require a
separate reconciliation/Edge withdrawal workflow, never this unpublished-plan endpoint.

PostgreSQL row locks provide production serialization. SQLite is a test backend;
real multi-process PostgreSQL race tests remain a deployment acceptance requirement.

Rollout: stop/quiesce old execute workers before the transactional status-constraint
migration and new code start. Old workers do not recognize CANCELLED/DISPATCHING and
must not coexist. Existing pending records predate the durable barrier; verify their
worker/log history before cancelling them. This migration cannot retroactively prove
that no old process published and then rolled back its database transaction.
