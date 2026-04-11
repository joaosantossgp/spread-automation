# Parallel Lanes Governance

## Rule of thumb
One task equals one owner, one branch, one worktree, and one PR.

## Lane ownership
Define lane ownership by path patterns and keep ownership explicit.

## Mandatory triage
Before starting executable work:
- check open tasks in your lane,
- check cross-lane child tasks,
- check open PRs and pending consumption states.

## Parent and child tasks
- Planning epic is a roadmap container only. It never replaces an executable parent task and must never be referenced in `Parent task`.
- Executable parent task is a `kind:task` issue that coordinates cross-lane delivery and owns the integration point.
- Child task is a cross-lane task that points to an executable parent task and is consumed by the parent lane.
- Standalone task has no executable parent task. It may still reference a planning epic for roadmap grouping.
- Use child tasks when one lane needs write access from another lane.
- Parent task tracks child tasks and stays blocked until delivery is consumed.
- Parent lane must match child requester lane.
- Parent status must stay blocked or awaiting-consumption while child is pending.

## Critical paths
Keep path-policy.json as versioned source of truth for:
- allowed lanes per path
- minimum risk by critical group
- draft and compatibility requirements

Critical groups should not overlap on the same changed file.

## Domain separation
Define prohibited domain mixes to avoid unsafe cross-domain PRs.

## Merge discipline
Prefer squash merge for short-lived task branches.
Require green checks and linked issue closure confirmation.
Do not mark a task as complete while PR is still open.
For all AI workflows, completion is allowed only after PR merge and linked task issue closure.

## Safety
- Never bypass required checks by default.
- Never auto-change protected Git settings without explicit confirmation.
