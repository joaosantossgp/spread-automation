#!/usr/bin/env bash
set -euo pipefail

repo="${1:-}"
default_branch="${DEFAULT_BRANCH:-main}"
required_checks="${REQUIRED_CHECKS:-}"
apply_branch_protection="${APPLY_BRANCH_PROTECTION:-false}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found in PATH: $1" >&2
    exit 1
  fi
}

resolve_repo() {
  if [[ -n "$repo" ]]; then
    printf '%s\n' "$repo"
    return
  fi

  gh repo view --json nameWithOwner --jq .nameWithOwner
}

upsert_label() {
  local repo_name="$1"
  local name="$2"
  local color="$3"
  local description="$4"

  if gh label list --repo "$repo_name" --limit 200 | cut -f1 | grep -Fxq "$name"; then
    gh label edit "$name" --repo "$repo_name" --color "$color" --description "$description" >/dev/null
  else
    gh label create "$name" --repo "$repo_name" --color "$color" --description "$description" >/dev/null
  fi
}

require_command gh

repo_name="$(resolve_repo)"

while IFS='|' read -r name color description; do
  upsert_label "$repo_name" "$name" "$color" "$description"
done <<'EOF'
kind:task|0e8a16|Executable task issue
kind:epic|5319e7|Planning umbrella for multiple tasks
status:ready|fbca04|Task contract is ready for execution
status:in-progress|1d76db|Work is active or PR is open
status:blocked|d93f0b|Task is blocked by dependency or decision
status:awaiting-consumption|c5def5|Child task delivered and awaits requester validation
status:completed|0e8a16|Merged and closed
priority:p0|b60205|Highest priority
priority:p1|d93f0b|High priority
priority:p2|fbca04|Normal priority
priority:p3|cccccc|Lower priority
area:ui|0052cc|Desktop UI and interaction flow
area:engine|5319e7|Runtime and orchestration
area:finance|006b75|Financial processing and mapping
area:data|0e8a16|Data ingestion and sources
area:governance|bfd4f2|Governance, CI, and repository operations
area:docs|0075ca|Documentation changes
risk:safe|0e8a16|Isolated write-set
risk:shared|fbca04|Shared or critical paths
risk:contract-sensitive|b60205|Public contract or compatibility-sensitive change
lane:app-ui|0052cc|App UI lane
lane:engine-finance|006b75|Engine finance lane
lane:ops-quality|5319e7|Ops and quality lane
EOF

gh api --method PATCH "repos/$repo_name" \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=false \
  -f delete_branch_on_merge=true \
  -f allow_auto_merge=false \
  -f has_issues=true \
  -f has_projects=false \
  -f has_wiki=false >/dev/null

echo "Labels and repository merge settings applied to $repo_name."

if [[ "$apply_branch_protection" != "true" ]]; then
  echo "Branch protection not changed. Re-run with APPLY_BRANCH_PROTECTION=true after the first PR exposes the exact check context."
  exit 0
fi

if [[ -z "$required_checks" ]]; then
  echo "Branch protection requires REQUIRED_CHECKS to be set." >&2
  exit 1
fi

json_file="$(mktemp)"
trap 'rm -f "$json_file"' EXIT
cat >"$json_file" <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["$required_checks"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF

gh api --method PUT "repos/$repo_name/branches/$default_branch/protection" --input "$json_file" >/dev/null
echo "Branch protection applied to $default_branch with checks: $required_checks"
