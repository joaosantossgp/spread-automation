# spread_automation

Automates filling Excel Spread (credit analysis) workbooks from CVM financial data (DFP/ITR).
João works in credit analysis; the Spread is the standard banking template.

## Critical facts (non-inferrable from code)

- **Spread grid**: columns D/F/H/J are annual data; L is quarterly. Columns A/C/E/G/I/K are hidden separators — never write to them.
- **SKIP set**: rows 199, 209, 210, 213 are excluded from the main scan and filled by specialized functions (DFC, DMPL). If the Spread template changes, these must be updated.
- **Matching hierarchy**: Camada 1 (exact CD_CONTA CVM match via `core/conta_map.py`) has priority; Camada 2 (numeric value fallback) activates when Layer 1 returns None or zero.
- **`is_trim` flag**: quarterly periods change column names in the source, trigger manual DRE (`DRE_SPREAD_MAP`), and select a different DMPL tab. It affects nearly every module.
- **Unmapped accounts** (deliberate): debt by currency (MN/ME), fixed assets, Reserva de Capital — CVM and Spread taxonomies are orthogonal; don't attempt to map these.
- **DFC filter**: always restrict DFC regex to `Codigo Conta` starting with `"6.01"` to avoid capturing financing-activity amortizations (section 6.03).
- **Receita convention**: CVM 3.01 always maps to "Vendas Mercado Externo" in the Spread (João's convention), regardless of label.

## Governance

Issue-first workflow. Work in a dedicated worktree and branch. See [AGENTS.md](AGENTS.md) for the full operational contract and lane rules.

## Context loading

Load on demand — do not pre-read unless the task requires it:
- [CONTEXT.md](CONTEXT.md) — full domain reference (pipeline, Spread layout, CVM structure, module architecture)
- [MEMORIADASIA.md](MEMORIADASIA.md) — session history, past bugs fixed, decisions taken by João
- [docs/architecture/](docs/architecture/) — design decisions and data model
- [CONTRIBUTING.md](CONTRIBUTING.md) — lane ownership and contribution guidelines

## Context Compaction

When compacting, always preserve:
- Files modified in this session (list with a brief note on what changed)
- Design decisions and their rationale
- Active task/issue number and its current status
- Any test failures and their identified root cause
- The matching hierarchy: Camada 1 (CD_CONTA) → Camada 2 (numeric value)
- Governance rules explicitly invoked during the session
