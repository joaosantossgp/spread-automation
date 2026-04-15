# Contributing

This repository uses a lane-based governance model. Treat GitHub Issues as the source of truth for executable work and keep every change inside an explicit task contract.

## Read First

- `AGENTS.md` is the operational contract for contributors and coding agents.
- `docs/governance/parallel-lanes.md` explains the multi-lane workflow and child-task rules.
- `.github/guardrails/path-policy.json` is the authoritative map for lane ownership, critical groups, and draft requirements.

## Lanes And Ownership Boundaries

Check `.github/guardrails/path-policy.json` before choosing a lane or write-set. Current boundaries are:

| Lane | Primary responsibility | Typical paths |
| --- | --- | --- |
| `app-ui` | Desktop UI and presentation assets | `app/**`, `themes/**` |
| `engine-finance` | Financial runtime, ingestion, mapping, spread, validation, and templates | `core/**`, `processing/**`, `ingestion/**`, `mapping/**`, `mapping_tables/**`, `spread/**`, `validation/**`, `engine/**`, `templates/**` |
| `ops-quality` | Governance, docs, scripts, CI/CD, templates, and root markdown | `.github/**`, `.claude/**`, `docs/**`, `scripts/**`, `*.md`, `LICENSE`, `.gitignore` |
| `master` | Cross-cutting orchestrator: bug fixes, unblocking, and broad corrections. Exempt from domain mix restrictions. Does NOT own governance (`critical-bootstrap` stays with `ops-quality`). Supports `master.plan` read-only mode for task planning. | `app/**`, `themes/**`, `core/**`, `processing/**`, `ingestion/**`, `mapping/**`, `mapping_tables/**`, `spread/**`, `validation/**`, `engine/**`, `templates/**` |

Shared-governance paths such as `CONTRIBUTING.md`, `docs/**`, `.claude/**`, and `.github/ISSUE_TEMPLATE/**` require `risk:shared` and must open in a draft PR.

## Issue-First Workflow

1. Find or create an open task issue before editing versioned files.
2. Make sure the issue has one label from each required family: `kind:*`, `status:*`, `priority:*`, `area:*`, `risk:*`, `lane:*`.
3. Make sure the issue body declares the required contract fields:
   - `Current owner`
   - `Official lane`
   - `Task workspace`
   - `Expected write-set`
   - `Risk classification`
4. If the task needs another lane to change its owned paths, open a formal child task instead of expanding the write-set informally.
5. Create a dedicated branch and worktree for the task.
6. Open one official PR for the task with `Closes #<issue-number>` in the body.

## Jules-Only PR-First Intake

The standard flow stays issue-first for humans and normal agents. There is one exception: PRs published automatically by Jules (Google Labs).

For Jules-originated PRs:

1. Let Jules publish the PR first.
2. GitHub Actions detects the Jules body marker, applies `source:jules`, and creates the task issue automatically when one is missing.
3. The workflow syncs the normal task contract on that issue:
   - required labels
   - `Current owner`
   - `Official lane`
   - `Task workspace`
   - `Expected write-set`
   - `Risk classification`
   - `Source PR`
4. The workflow updates the Jules PR body to include `Closes #<issue-number>`.
5. If the changed paths require draft status, configure repository secret `JULES_GOVERNANCE_TOKEN` to let the workflow convert the PR to draft automatically. Without that secret, the check fails explicitly and the PR must be converted manually.
6. Do not reuse this exception for non-Jules PRs.

## Required Issue Fields

Every executable task must declare:

- `Current owner`: the human or agent currently responsible.
- `Official lane`: the lane that owns the task.
- `Task workspace`: the dedicated worktree path.
- `Expected write-set`: the exact files or globs the task may change.
- `Risk classification`: `safe`, `shared`, or `contract-sensitive`.

For Jules intake tasks, also declare:

- `Source PR`: the Jules PR being governed, for example `#44`. Use `n/a` for normal issue-first tasks.

Child tasks must also declare:

- `Parent task` (`Task mae`)
- `Requester lane` (`Lane solicitante`)
- `Consumption criteria` (`Criterio de consumo`)

Use `n/a` only for fields that are intentionally not applicable.

## Branch And Worktree Naming

- Branch pattern: `<lane>/<issue-number>-<slug>`
- Worktree pattern: `.claude/worktrees/<lane>/<issue-number>-<slug>/`
- Rule: one task, one owner, one branch, one worktree, one PR

Example for issue `#38` in `ops-quality`:

- Branch: `ops-quality/38-contributing-templates`
- Worktree: `.claude/worktrees/ops-quality/38-contributing-templates/`

## PR Lifecycle

1. Open the PR as `draft` when the write-set touches shared-governance or other critical paths.
2. Keep the linked issue at `status:in-progress` while the PR is open or waiting for review.
3. Let `validate-pr-issue-contract` enforce branch naming, issue metadata, write-set coverage, and lane/path policy.
4. Mark the PR ready only after the task contract is correct and the implementation is ready for merge.
5. Merge only after required checks are green and required approvals are satisfied.
6. Confirm the linked issue is closed and the branch/worktree are cleaned up before reporting completion.

Pull requests close task issues, not epics.

## Status Semantics

- `status:ready`: the task contract is complete and execution can start now.
- `status:in-progress`: work is active, or the PR is open and still pending completion gates.
- `status:blocked`: the task cannot proceed because it depends on an unresolved external action, decision, or child task.
- `status:awaiting-consumption`: a child task delivered its change and the requester lane still needs to validate or consume it.
- `status:completed`: use only after PR merge and linked issue closure are both confirmed.

## Child Tasks And Cross-Lane Changes

- Open a child task whenever work crosses lane ownership.
- Keep the parent task in `status:blocked` or `status:awaiting-consumption` while the child task is pending or waiting for requester validation.
- Do not expand a task into another lane's write-set without explicitly declaring that dependency.

## Validation And Completion

Before merge:

- verify changed files stay inside the declared write-set
- verify the lane matches the owned paths in `.github/guardrails/path-policy.json`
- verify required checks are green
- verify the PR body closes the linked task issue

After merge:

- confirm the linked issue is closed
- confirm status is `status:completed`
- remove the task worktree and local branch if they are no longer needed

## Context Compaction Protocol

When Claude's context window fills and automatic compaction occurs, preserve:
- The active task issue number and its current status
- Governance rules or lane ownership decisions invoked during this session
- Design decisions taken and their rationale
- Test failures and their identified root cause
- Files modified in this session (with brief note on what changed)
- References to MEMORIADASIA.md and CONTEXT.md (always reload these)

Discard at compaction time:
- Exploration logs and discovery work
- Intermediate attempts and failed approaches
- Full session transcripts (keep only the decision summary)

**Memory file rule:** MEMORIADASIA.md grows session-by-session. After 3 active sessions, compress older session logs into a 2-line summary and move to "Prior Session Archive" section. Keep current state and permanent decisions always available.

## References

- `AGENTS.md`
- `docs/governance/parallel-lanes.md`
- `.github/guardrails/path-policy.json`
- `.github/PULL_REQUEST_TEMPLATE.md`
