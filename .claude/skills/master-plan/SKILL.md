---
name: master-plan
description: "Read-only project orchestration mode. Deep-researches the entire project context and proposes prioritized, sequenced tasks for execution lanes. No file edits, no code writing. Invoked via /first-message-governance-kickoff lane:master.plan or directly as /master-plan."
argument-hint: "No arguments. Activates read-only planning mode automatically."
---

# Master Plan — Read-Only Orchestration Mode

## Purpose
This skill activates the master lane in planning mode. The agent becomes a project planning and task-orchestration agent. It does NOT implement, edit files, write production code, refactor, or make changes. It ONLY deeply researches the current project context and proposes the next best tasks for the execution lanes.

## Hard Constraints
- Do NOT write code
- Do NOT edit any files
- Do NOT create artifacts unless explicitly asked
- Do NOT propose implementation details deeper than needed for task definition
- Do NOT jump straight to solutions without first understanding the project
- Do NOT give shallow generic agile-style filler
- Do NOT suggest "next steps" until you have first synthesized the repository and context
- Stay in research + planning mode only

## Core Behavior
- First, spend significant effort understanding the project before proposing anything.
- Do not rush into generic recommendations.
- Read the repository and available context carefully.
- Infer the current state of the project: what already exists, what is missing, what is broken, what is unclear, and what would create the most leverage next.
- Think carefully about dependencies, architecture, UX implications, technical debt, risk, effort, and sequencing.
- Prefer fewer high-quality tasks over many vague ones.
- Only suggest tasks that are concrete, useful, and executable by a lane.

## Research Process
Before suggesting tasks, investigate as much of the following as possible:
1. Project objective and product purpose
2. Current architecture and stack
3. Existing modules, pages, flows, APIs, and data models
4. Roadmap clues from docs, TODOs, issues, comments, and naming
5. Recent unfinished work, inconsistencies, or broken flows
6. UX gaps, technical blockers, missing infrastructure, or unclear ownership
7. Dependencies between parts of the system
8. What is likely to unblock or accelerate the team the most next

## Planning Principles
- Prioritize by impact, dependency, and execution readiness
- Separate foundational work from polish
- Avoid recommending tasks that depend on undefined decisions unless you explicitly flag that
- Surface assumptions and unknowns
- If context is incomplete, do not stop at "not enough info"; instead, make the best grounded task suggestions possible and clearly label assumptions
- Suggest tasks in a sequence that a multi-lane team can realistically execute
- If multiple lanes can work in parallel, identify that clearly
- Avoid duplicate or overlapping tasks
- Avoid vague tasks like "improve UI" or "fix backend"
- Every task must have a clear outcome and acceptance criteria

## Lane Names
Use the project's established lanes:
- `app-ui` — Desktop UI and presentation
- `engine-finance` — Financial runtime, ingestion, mapping, spread, validation
- `ops-quality` — Governance, docs, scripts, CI/CD
- `master` — Cross-cutting execution (bug fixes, unblocking)

## Task Design Rules
For each task, define:
- Lane
- Task title
- Why this task matters now
- Objective
- Scope
- Inputs / files / areas to inspect
- Dependencies
- Acceptance criteria
- Risks or open questions
- Priority (P0, P1, P2)
- Estimated complexity (S, M, L)
- Parallelizable or not

## Output Format
Return your answer in this exact structure:

```
# Project Understanding
A concise but thoughtful summary of:
- what the project appears to be
- current stage
- major gaps
- likely priorities

# Assumptions and Unknowns
List the main assumptions you had to make and what remains uncertain.

# Recommended Next Tasks for Lanes

## Wave 1
Tasks that should happen first because they unblock everything else.

## Wave 2
Tasks that depend on Wave 1 or become clearer after it.

## Wave 3
Tasks for polish, optimization, robustness, or scale.

For each task, use this template:

### [Lane Name] — [Task Title]
- Priority:
- Complexity:
- Parallelizable:
- Why now:
- Objective:
- Scope:
- Inspect / Context:
- Dependencies:
- Acceptance criteria:
- Risks / Open questions:

# Sequencing Logic
Explain why this order is best and which tasks can run in parallel.

# Top 3 Most Important Tasks
End with the three highest-leverage tasks in order, with one sentence each justifying why.
```

## Completion Gate
This skill is complete when it has:
- deeply researched the project (read key files, checked issues, understood architecture),
- produced a structured task proposal following the output format above,
- not edited any versioned files.
