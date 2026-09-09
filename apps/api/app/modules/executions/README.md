# executions

Run, step, attempt, lease, durable waits, outbox và recovery.

## Current state
M1 adds only the persisted `OutboxEvent` foundation so future domain writes can share a transaction with notification/task intent. Workflow runs, steps, attempts, worker leases and durable waits are **not implemented yet**; they belong to M2.

Core/worker authorization and restart semantics remain mandatory per `docs/06_BACKEND_DATABASE_AUTH.md`.
