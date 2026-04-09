param(
  [Parameter(Mandatory = $true)]
  [int]$Issue,

  [Parameter(Mandatory = $true)]
  [string]$Slug,

  [Parameter(Mandatory = $true)]
  [string]$Lane,

  [string]$BaseBranch = "main",
  [string]$Root = ".claude/worktrees",
  [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$inside = git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0 -or "$inside".Trim() -ne "true") {
  throw "Run this script inside a git repository."
}

$slugSafe = $Slug.Trim().ToLower() -replace "[^a-z0-9-]", "-"
$branch = "$Lane/$Issue-$slugSafe"
$worktreePath = Join-Path $Root "$Lane/$Issue-$slugSafe"

if (-not (Test-Path $worktreePath)) {
  throw "Worktree not found: $worktreePath"
}

if (-not $Force) {
  $merged = git branch --merged "$BaseBranch" --list "$branch"
  if (-not "$merged".Trim()) {
    throw "Branch $branch is not merged into $BaseBranch. Use -Force if you need explicit override."
  }
}

git worktree remove "$worktreePath" -f

$branchExists = git show-ref --verify --quiet "refs/heads/$branch"
if ($LASTEXITCODE -eq 0) {
  if ($Force) {
    git branch -D "$branch"
  } else {
    git branch -d "$branch"
  }
}

Write-Output "Removed worktree: $worktreePath"
Write-Output "Removed branch: $branch"
