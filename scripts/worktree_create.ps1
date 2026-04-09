param(
  [Parameter(Mandatory = $true)]
  [int]$Issue,

  [Parameter(Mandatory = $true)]
  [string]$Slug,

  [Parameter(Mandatory = $true)]
  [string]$Lane,

  [string]$BaseBranch = "main",
  [string]$Root = ".claude/worktrees"
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

if (Test-Path $worktreePath) {
  throw "Worktree already exists: $worktreePath"
}

$parent = Split-Path $worktreePath -Parent
if (-not (Test-Path $parent)) {
  New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$remoteBase = "origin/$BaseBranch"
$baseExists = git show-ref --verify --quiet "refs/remotes/$remoteBase"
if ($LASTEXITCODE -eq 0) {
  git worktree add "$worktreePath" -b "$branch" "$remoteBase"
} else {
  git worktree add "$worktreePath" -b "$branch" "$BaseBranch"
}

Write-Output "Created worktree: $worktreePath"
Write-Output "Branch: $branch"
