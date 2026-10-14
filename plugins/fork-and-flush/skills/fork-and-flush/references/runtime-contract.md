# Common runtime contract

Map these capabilities to the host's supported tools; do not invent tool names.

| Operation | Required behavior |
|---|---|
| Snapshot | Freeze the leader's authorized workspace, including relevant dirty files |
| Isolate | Produce independent writable copies from one snapshot |
| Start fresh | Create a new conversation without parent transcript or summary |
| Continue | Resume the selected worker's session against its existing workspace |
| Stop | Enforce a branch limit and terminate associated work before evaluation |
| Evaluate | Execute a fixed evaluator and preserve its inputs and output |
| Account | Aggregate usage across all branches, including failures and retries |

Filesystem isolation and conversation isolation are independent. Separate session
IDs do not prove independent files; separate directories do not prove fresh prompts.
Inspect both. Avoid copying chat caches or a coordinator's rationale into the task
workspace. Existing research artifacts remain part of the inherited workspace.

Keep an append-only run record outside the worker directories. A useful result row:

```json
{
  "round": 1,
  "branch": "b1",
  "session_id": "host-session-id",
  "workspace": "runs/r1/b1",
  "parent_snapshot": "sha256-of-snapshot-manifest",
  "artifact": "runs/r1/b1/candidate.py",
  "artifact_sha256": "sha256-of-candidate",
  "valid": true,
  "score": 42,
  "direction": "minimize",
  "budget_unit": "agent-seconds",
  "allocated": 60,
  "used": 48.2,
  "status": "completed"
}
```

The identifiers are examples, not literal hashes. Record the evaluator version,
test seeds, and global budget once at run level. Cap process trees or remote jobs,
not just the shell that launched them. SDK cancellation, containers, or job-level
timeouts may be appropriate depending on the host.

If only fresh serial sessions are possible, disclose the lack of concurrency and
preserve comparable aggregate allocations. If no fresh sessions or independent
workspaces are possible, produce a plan and explain the unsupported operation.

The skill can be installed wherever a host reads the Agent Skills format. Installing
it does not add orchestration capabilities to that host. A product belongs in the
tested compatibility table only after its actual workflow has been exercised.
