# Operators Runbook

Use this document as your operational playbook after governance bootstrap.

## Daily Routine
1. Check open tasks in your lane.
2. Check child tasks received and requested.
3. Check open PRs linked to those tasks.
4. Resolve pending consumption before opening new cross-lane work.

## Discovery-first Rule
Before any apply or enforcement changes, review:
- existing `.github` governance artifacts,
- governance docs and runbooks,
- repository structure ownership map.

## Task Execution Flow
1. Open task issue with required labels and metadata.
   Use `Planning epic` only for roadmap grouping.
   Use `Executable parent task` only for cross-lane child tasks.
2. Create worktree and task branch.
3. Implement in dedicated worktree only.
4. Open one PR with linked issue closure line.
5. While PR is open, keep issue status in-progress and report pending review/approval gates.
6. Complete PR only after required checks are green and required approvals are done.
7. Confirm linked issue closure and cleanup worktree before declaring task complete.

## Jules PR Intake
Use this flow only for PRs published automatically by Jules.

1. Confirm the PR is Jules-originated by its body marker or `source:jules` label.
2. Let `.github/workflows/jules-pr-governance.yml` create the task issue automatically when one is missing.
3. Confirm the workflow synchronized `Source PR`, lane, workspace, write-set, and risk on the created issue.
4. Confirm the workflow updated the PR body with `Closes #<issue-number>`.
5. If the PR touches shared or critical paths, set repository secret `JULES_GOVERNANCE_TOKEN` so the workflow can convert it to draft automatically. Without that secret, the workflow fails explicitly and an operator must convert the PR to draft manually.
6. Merge only after the linked issue, write-set, lane, and risk checks pass like any other governed PR.

## Task Modeling
- Planning epic: roadmap only, never referenced in `Parent task`.
- Executable parent task: a `kind:task` issue that owns integration and consumes child-task delivery.
- Child task: cross-lane task with `Requester lane`, `Consumption criteria`, and `Parent task` pointing to an executable parent task.
- Standalone task: normal executable task with `Parent task`, `Requester lane`, and `Consumption criteria` set to `n/a`.

## AI Handoff Rule
- Do not claim done when PR is still open, even if checks are green.
- Do not claim done when linked issue is still open.
- If blocked by external reviewer action, hand off with explicit blocker and next owner.

## Bootstrap Commands
- PowerShell dry-run:
  powershell -ExecutionPolicy Bypass -File scripts/bootstrap-governance.ps1 -RepoPath . -Mode dry-run
- PowerShell apply:
  powershell -ExecutionPolicy Bypass -File scripts/bootstrap-governance.ps1 -RepoPath . -Mode apply -OverwritePolicy preserve
- Bash dry-run:
  ./scripts/bootstrap-governance.sh --repo . --mode dry-run
- GitHub repo settings and labels:
  powershell -ExecutionPolicy Bypass -File scripts/bootstrap-github-settings.ps1
- GitHub repo settings and labels (bash):
  ./scripts/bootstrap-github-settings.sh
- Apply branch protection after the first guardrails run exposes the exact check name:
  powershell -ExecutionPolicy Bypass -File scripts/bootstrap-github-settings.ps1 -ApplyBranchProtection -RequiredChecks validate-pr-issue-contract

## Helper Commands
- Worktree create:
  powershell -ExecutionPolicy Bypass -File scripts/worktree_create.ps1 -Issue 27 -Slug sample-task -Lane ops-quality
- Worktree status:
  powershell -ExecutionPolicy Bypass -File scripts/worktree_status.ps1
- PR complete:
  powershell -ExecutionPolicy Bypass -File scripts/pr_complete.ps1 -Pr 28
- Worktree remove:
  powershell -ExecutionPolicy Bypass -File scripts/worktree_remove.ps1 -Issue 27 -Slug sample-task -Lane ops-quality

## Safety
- Do not skip required checks.
- Do not force-remove worktree without explicit approval.
- Do not use destructive Git reset commands.
- Do not auto-change protected or global Git settings without explicit approval.

## Escalation
If guardrails or apply fail:
1. inspect rollback guide,
2. restore from backup manifest,
3. rerun dry-run,
4. reattempt apply only after conflicts are resolved.

If GitHub settings drift:
1. rerun `scripts/bootstrap-github-settings.ps1`,
2. confirm labels and repo merge settings,
3. reapply branch protection with the live guardrail check context.

If issue modeling fails:
1. confirm whether the issue is a planning epic, executable parent task, child task, or standalone task,
2. never point `Parent task` to an epic,
3. keep same-lane work standalone unless there is a real cross-lane child-task dependency,
4. rerun the issue and PR guardrails after fixing the issue body.

## Validation History

| Date       | Task                                              | Result  | Notes                                       |
|------------|---------------------------------------------------|---------|---------------------------------------------|
| 2026-04-09 | #10 First guarded PR flow kickoff (ops-quality)   | passed  | First end-to-end guardrail validation cycle |
