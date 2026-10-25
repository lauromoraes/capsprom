# Persistent Remote Job Operations

Long or expensive remote commands must run through a persistent asynchronous
launcher that survives SSH disconnection. This rule does not grant remote
access and does not open any scientific execution gate. The active contract is
`configs/capsprom_remote_usage_policy_v3.yaml`.

## Before launch

Inspect `manifests/remote_jobs.json`, then query the authorized host for the
registered process, scheduler identifier, result path, state, and checkpoint.
Compare the command, working directory, versioned configuration hash, and
result identity with the proposed job. If an equivalent process or completed
result exists, do not launch another copy.

## Durable launch record

Before starting the process, assign a stable project job identifier and record
the server, launcher, exact command, working directory, configuration, log,
result paths, checkpoint paths, exit-code path, and start time. Use `nohup` plus
`setsid`, or the host scheduler when available. The remote wrapper must persist
the command exit code to a dedicated file using atomic replacement. A PID file
alone is insufficient because process identifiers may be reused and do not
show whether the command succeeded.

Immediately after launch, verify both the persistent process identity and the
declared log path. Update the registry atomically, report the identifier and
paths, and return without waiting for completion.

## Later checks and completion

There is no automatic monitoring between conversations. During a later
interaction with authorized host access, inspect every registered `pending` or
`running` job before starting equivalent work. Record the check time and report
progress from durable state or logs.

Mark a job `completed` only after the process has stopped, the persisted exit
code is zero, and every expected result, state, checkpoint, and integrity check
is present. On failure, preserve logs and resumable state, diagnose the cause,
and reuse the same scientifically equivalent job identity and checkpoints when
the runner supports recovery. Never erase failure evidence or duplicate work
merely because the SSH connection ended.
