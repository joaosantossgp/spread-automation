$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$inside = git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0 -or "$inside".Trim() -ne "true") {
  throw "Run this script inside a git repository."
}

Write-Output "Worktrees:"
git worktree list
Write-Output ""
Write-Output "Local branches:"
git branch --list
