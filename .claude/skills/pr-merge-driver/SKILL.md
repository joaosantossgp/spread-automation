---
name: pr-merge-driver
description: >
  Drives ALL open pull requests all the way to merge and closes their linked issues.
  By default processes every open PR — not just one. Use this skill whenever there are
  open PRs that haven't been merged yet, especially as the default next action after
  finishing implementation work. Trigger when the user says "merge this PR", "merge all
  PRs", "get this PR merged", "push this to main", "unblock the PR", "fix the CI",
  "resolve the conflict", or simply when you notice PRs that are open and ready.
  The skill handles every blocker: draft status, CI failures, merge conflicts, missing
  issue links, branch protection rules, and governance constraints. It doesn't stop until
  all PRs are merged and their issues are closed — or until a genuinely external
  dependency (mandatory human approval, product decision) is the only thing left.
---

# PR Merge Driver

Your job is to get **all** open PRs merged and their linked issues closed. Process every
open PR — not just the most recent one. Treat each as a complete cycle:
diagnose → order → unblock → merge → close issue. Don't stop partway through.

---

## Step 1 — List and read all open PRs

List every open PR:

```bash
gh pr list --state open --json number,title,headRefName,isDraft,mergeable,mergeStateStatus,labels
```

If the user specified a specific PR number, process only that one. Otherwise process
all of them.

Read each PR in full before acting on any:

```bash
gh pr view <number> --json number,title,body,state,isDraft,mergeable,mergeStateStatus,\
statusCheckRollup,reviewDecision,baseRefName,headRefName,labels,closingIssuesReferences
```

Note: `closingIssuesReferences` contains issues the PR closes automatically on merge
(GitHub resolves keywords like "Closes #N", "Fixes #N", "Resolves #N" in the PR body).

---

## Step 1b — Determine merge order

Before touching anything, check for file overlaps across all open PRs:

```bash
gh pr diff <number> --name-only   # repeat for each PR
```

Build a dependency graph:
- PRs that touch **no overlapping files** can be merged in any order (or in parallel).
- PRs that touch **overlapping files** must be merged sequentially — merge the simpler /
  less conflicted one first, then re-fetch and update the other after each merge.

Merge order heuristic: fewer changed files → merge first. More complex / larger diff →
merge last (it will need to absorb conflicts from earlier merges anyway).

Cascade rule: **after every merge, re-fetch main and check every remaining PR for new
conflicts** before proceeding. A merge that lands can conflict a previously clean PR.

---

## Step 2 — Identify the linked issue (per PR)

A PR and its issue form a single unit of work. Find the issue before doing anything else.

**Where to look (in priority order):**

1. `closingIssuesReferences` from the PR JSON (most reliable)
2. Keywords in the PR body: `Closes #N`, `Fixes #N`, `Resolves #N`
3. PR title containing `#N`
4. Branch name pattern like `feature/issue-42-description` or `fix/42`
5. Ask the user if still not found

If the PR body doesn't already contain a closing keyword:

```bash
gh pr edit <number> --body "$(gh pr view <number> --json body -q .body)

Closes #<issue-number>"
```

This ensures GitHub closes the issue automatically on merge. Always do this when the
link is missing — it's a zero-cost fix that removes a manual step later.

---

## Step 3 — Diagnose the blocker (per PR)

Run a full health check. Identify every reason the PR is not yet mergeable:

```bash
gh pr view <number> --json state,isDraft,mergeable,mergeStateStatus,statusCheckRollup,\
reviewDecision,commits,baseRefName,headRefName
```

Map the status to one of the cases below and handle each one. A PR can have more than
one blocker — fix all of them.

---

## Step 4 — Handle each blocker type

### 4a. PR is in draft

The author marked it as not ready. Ask the user whether to promote it:

```bash
gh pr ready <number>
```

Don't promote silently if the draft status seems intentional (e.g., PR description says
"WIP" or has open TODO comments). If unsure, ask.

**Governance-required draft (Jules PRs / critical paths):** Some CI workflows require
the PR to be in draft while validation runs, then promote it only after checks pass.
In this case: keep the PR in draft, push a commit to trigger a fresh CI run (see 4b),
wait for green, *then* promote and merge immediately. Do not promote before CI passes —
promoting triggers another CI run that will see `isDraft: false` and re-fail the check.

### 4b. CI / checks failing

Read the failing checks:

```bash
gh pr checks <number>
```

For each failure, read the logs:

```bash
gh run view <run-id> --log-failed
```

Then decide: can you fix it, or is it an external flake?

**Fix it yourself when:**
- Test failure is caused by your recent code change
- Lint/format error (run the formatter and push a fix commit)
- Missing env variable or config that you can supply
- Type error or import error you introduced

**Re-trigger when:**
- The failure is clearly a transient infrastructure error (network timeout, runner OOM,
  flaky test with `[flaky]` label or known issue). Re-run with:

```bash
gh run rerun <run-id> --failed
```

**Critical: stale CI context.** GitHub Actions captures PR state (including `isDraft`,
branch HEAD, etc.) at trigger time. A `gh run rerun` replays the original context — it
does NOT reflect changes made since then (e.g., a draft conversion that happened after
the run was triggered). If the failure reason depends on current PR state rather than
code, push a fresh commit instead of re-running:

```bash
# empty commit to force a new CI trigger with current PR state
git commit --allow-empty -m "ci: trigger fresh check"
git push origin <head-branch>
```

**Escalate when:**
- External service is down and tests require it
- Flaky test is persistent and you don't own the test file — document this and proceed
  only if the repo allows merge with known-flaky tests

After a fix commit or fresh push, wait for CI to re-run before moving on:

```bash
gh run watch
```

### 4c. Merge conflicts

Use a temporary worktree to avoid polluting the main checkout:

```bash
git fetch origin
git worktree add .claude/worktrees/pr<number>-fix origin/<head-branch>
cd .claude/worktrees/pr<number>-fix
git checkout -b <head-branch>
git merge origin/<base-branch>
# resolve conflicts, then:
git add <resolved-files>
git commit -m "chore: resolve merge conflicts with <base-branch>"
git push origin <head-branch>
git worktree remove .claude/worktrees/pr<number>-fix
```

When resolving conflicts:
- Preserve the intent of both sides; don't silently drop one
- If the conflict is in a file you don't fully understand, describe the conflict to the
  user and ask how to resolve it before committing
- After pushing, wait for CI to re-run

**Cascading conflicts (multi-PR batches):** Each merge advances main. The next PR in
the queue may now conflict even if it was clean before. After every merge, re-run
`gh pr view <next-number> --json mergeable,mergeStateStatus` and re-fetch before
attempting the next merge. Expect to resolve one conflict round per PR that touches
shared files.

### 4d. Review not approved / changes requested

```bash
gh pr view <number> --json reviewDecision,reviews
```

- If `reviewDecision` is `CHANGES_REQUESTED`: read the review comments and address them.
  Push a fix commit. Then re-request review:

```bash
gh pr review <number> --request-review <reviewer>
```

- If `reviewDecision` is `REVIEW_REQUIRED` and no review exists: check who the required
  reviewers are and notify the user — this is a human dependency you cannot bypass.
- If the user has merge permissions and the repo allows self-merge after addressing
  feedback, confirm with the user before proceeding without a new approval.

### 4e. Branch protection / governance rules

```bash
gh api repos/{owner}/{repo}/branches/<base>/protection
```

Common rules and how to handle them:

| Rule | Response |
|------|----------|
| Required status checks not passed | Wait or fix CI (→ 4b) |
| Required number of approvals not met | This is a human dependency — surface it clearly |
| Dismiss stale reviews on push | After your fix push, the approval is gone — request re-review |
| Require signed commits | Sign commits with `git commit -S` |
| Restrict pushes to certain users | You cannot bypass this — escalate to user |

### 4f. Overlap or conflict with another open PR

```bash
gh pr list --state open --json number,title,headRefName,baseRefName
```

If another PR touches the same files:
- Check if one should be merged before the other (ordering)
- If they are in a dependency chain, surface this to the user
- Don't rebase/restructure another team member's PR without permission

### 4g. Missing or ambiguous issue link

Already handled in Step 2. If no issue was found and the user doesn't know which issue
this PR relates to, document this in the PR body:

> Note: No linked issue found. Merged standalone.

Don't delay the merge to track down an issue that doesn't exist.

---

## Step 5 — Merge the PR

Only merge when all checks pass and all required reviews are in:

```bash
gh pr merge <number> --squash --delete-branch
```

Try `--squash` first (preferred for short-lived task branches). If the repo disallows
squash, try `--merge`. If the repo disallows merge commits, try `--rebase`. If all fail
with "base branch policy prohibits the merge", try `--auto` (auto-merge when ready). If
`--auto` is also disabled, the merge must be triggered through the repo's own automation
(e.g., an auto-merge workflow) — promote the PR to ready and wait for it to land.

If the merge fails due to a race condition with another concurrent merge, re-run the
health check from Step 3 and handle the new state (usually a new conflict).

After each merge, immediately proceed to Step 6 for that PR before starting the next.

---

## Step 6 — Verify the issue was closed

Wait a few seconds for GitHub to process the merge event, then:

```bash
gh issue view <issue-number> --json state,stateReason
```

**If the issue is now closed:** record the result and move on to the next PR.

**If the issue is still open:**

Possible reasons:
- The closing keyword was missing or malformed — check the PR body
- The base branch doesn't match the repo's default branch (GitHub only auto-closes from
  the default branch)
- The repo's auto-close feature is disabled
- The issue was manually reopened after an earlier premature auto-close; GitHub will not
  re-fire the auto-close event — close it manually

Close it manually:

```bash
gh issue close <issue-number> --reason completed --comment \
  "Closed by #<pr-number> merged in <commit-sha>."
```

---

## Step 7 — Loop: next PR

After each PR is merged and its issue is closed, immediately move on to the next PR in
the merge order determined in Step 1b.

Before starting the next PR:
1. `git fetch origin` — main has advanced; remaining PRs may now have new conflicts.
2. Re-check `gh pr view <next-number> --json mergeable,mergeStateStatus`.
3. If new conflict: go to Step 4c before anything else.

Repeat Steps 2–7 for every PR in the queue. Do not stop after the first merge.

---

## Step 8 — Final report to the user

After all PRs are processed, give a single consolidated summary:

```
✅ PR #<N> merged — "<PR title>"
   Issue #<M> closed.   Commit: <sha>

✅ PR #<N> merged — "<PR title>"
   Issue #<M> closed.   Commit: <sha>

⚠️  PR #<N> blocked — "<PR title>"
   Reason: <why it couldn't be merged>
   Required action: <what the user needs to do>
```

Include a brief note for any judgment call made on the user's behalf (conflict
resolution strategy, draft promotion, file removal, etc.).

---

## When to stop and escalate

Stop and clearly explain the situation when:

- **Mandatory human approval is required** and no workaround exists
- **A product/design decision** is needed to resolve a conflict
- **The user lacks push access** to the target branch and can't grant it
- **CI depends on a secret** that isn't configured and only the user can add it
- **The PR modifies files in a protected path** and you don't have permission

In these cases, tell the user exactly what is blocking progress, what they need to do,
and how to continue once they've done it. Then continue with other PRs in the queue
that are not blocked — don't stop the entire batch for one blocked PR.

---

## Operating principles

- **Process all PRs, not just one.** Unless the user explicitly asks for a single PR,
  work through every open PR in the queue.
- **Determine order before acting.** Build the dependency graph from file overlaps
  before touching any branch. Merging out of order creates avoidable cascading conflicts.
- **Diagnose precisely before acting.** Read every PR, its checks, its reviews, and the
  branch protection rules before touching anything.
- **Smallest change that unblocks.** A one-line fix to a test is better than a refactor.
- **Fresh push beats rerun for state-dependent CI.** GitHub Actions captures PR state at
  trigger time. If a check fails because of PR state (draft, HEAD sha, file list), a
  rerun will repeat the same failure — push a fresh commit instead.
- **Draft before push, promote after green.** For repos where governance CI requires
  draft status during validation: convert to draft first, then push (so the CI run sees
  `isDraft: true`), wait for green, then promote and merge immediately.
- **Preserve governance.** Never bypass required reviews or branch protections by
  exploiting loopholes. If a rule exists, respect it. Fix the root cause (wrong lane,
  incorrect write-set, missing issue link) rather than patching the policy file.
- **Always verify the issue closed.** Don't assume the keyword worked — check the issue
  state after merge. If the issue was reopened manually between merge and verification,
  close it manually.
- **Be transparent.** If you make a judgment call (conflict resolution, draft promotion,
  merge order, file removal), say so briefly in the final report.
