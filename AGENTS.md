# AGENTS.md

Operational contract for contributors and coding agents.

## Source of truth
- Backlog lives in GitHub Issues.
- Pull requests close task issues, not epics.

## Discovery-first startup
At the start of each executable chat:
- check open tasks in your lane,
- check child tasks received from other lanes,
- check child tasks requested by your lane,
- check open PRs linked to those issues,
- resolve awaiting-consumption before expanding cross-lane scope.

## Mandatory flow
1. Find or create an open task issue before changing versioned files.
2. Ensure required labels exist: kind, status, priority, area, risk, lane.
3. Ensure issue body includes owner, lane, workspace, write-set, and risk.
4. Work in a dedicated worktree and branch.
5. Open a single official PR with Closes #<issue-number> in the body.
6. Keep task status in-progress while PR is open or waiting review.
7. Complete PR only after required checks are green and required approvals are done.
8. Confirm linked issue closure and branch cleanup before declaring task complete.

## Jules PR exception
- This exception exists only for PRs published automatically by Jules (Google Labs).
- Jules may publish a PR before a task issue exists.
- After a Jules PR opens, create the task issue, record the source PR, declare lane/workspace/write-set/risk, and update the PR body with `Closes #<issue-number>`.
- Keep the Jules PR in draft until the post-publication governance intake is complete.
- Do not use this exception for human, Codex, or other automation PRs.

## Branch and worktree
- Branch pattern: <lane>/<issue-number>-<slug>
- Worktree pattern: .claude/worktrees/<lane>/<issue-number>-<slug>/
- Rule: one task, one owner, one branch, one worktree, one PR.

## Parallel work protocol
- Interfaces are additive-only by default during parallel execution.
- Breaking contract changes require a dedicated contract-sensitive task.
- If write-set collision happens across tasks, declare dependency before continuing.

## Child tasks
- If work crosses lane ownership, open formal child tasks.
- Child tasks must include Task mae, Lane solicitante, and Criterio de consumo.
- Parent task remains blocked or awaiting-consumption until requester confirms consumption.

## Risk policy
- safe: isolated write-set
- shared: shared or critical paths, draft PR required
- contract-sensitive: public contract changes, draft PR and compatibility section required

## Completion
A task is complete only when PR is merged and linked issue is closed.

## AI completion gate
- Never report task completion while PR is still open.
- Never finalize a task while the linked issue remains open.
- If external review or approval is pending, report the pending gate explicitly and keep the task open.

## Master lane

The `master` lane is the cross-cutting orchestrator with absolute write access to all application and engine paths. It exists for:
- fixing bugs that span multiple domains,
- unblocking work other lanes are hesitant to touch,
- executing next-step corrections across the codebase.

Master lane has two modes:
- **Execution mode** (`lane:master`): normal lane-aware execution with broad write access. Can touch `app/**`, `core/**`, `processing/**`, `engine/**`, and all other runtime/UI paths. Domain mix restrictions (`app-ui-with-engine-runtime`) are exempt for this lane.
- **Planning mode** (`lane:master.plan`): read-only orchestration. No file edits, no code changes. Deep project research and structured task proposals only.

**Governance exclusion:** The master lane does NOT own and CANNOT write to governance-critical paths (`critical-bootstrap`). That domain stays exclusively with `ops-quality`. This means master cannot modify `.github/workflows/**`, `.github/guardrails/**`, `.github/governance.config.yaml`, or bootstrap scripts.

## Safety constraints
- Required checks must stay green for merge completion.
- Never force-remove worktrees without explicit approval.
- Never use destructive Git reset commands.
