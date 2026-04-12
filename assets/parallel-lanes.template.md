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

## Jules intake exception
- The issue-first rule remains the default for all human, Codex, and non-Jules automation work.
- PRs published automatically by Jules are the only supported PR-first exception.
- After a Jules PR opens, create a task issue, record `Source PR`, and retrofit the normal lane/workspace/write-set/risk contract onto that task.
- The Jules PR must add `Closes #<issue-number>` after intake and stay draft until governance validation passes.
- Jules PRs do not need to follow the normal branch pattern; that exception does not apply outside the Jules flow.

## Parent and child tasks
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

## Safety
- Never bypass required checks by default.
- Never auto-change protected Git settings without explicit confirmation.
