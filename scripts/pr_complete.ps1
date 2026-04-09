param(
  [Parameter(Mandatory = $true)]
  [int]$Pr,

  [ValidateSet("squash", "merge", "rebase")]
  [string]$MergeMethod = "squash",

  [switch]$DeleteBranch
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
  throw "GitHub CLI (gh) is required for this script. Install gh and run `gh auth login`."
}

$mergeFlag = "--$MergeMethod"
$args = @("pr", "merge", "$Pr", $mergeFlag)
if ($DeleteBranch) {
  $args += "--delete-branch"
}

& gh @args
if ($LASTEXITCODE -ne 0) {
  throw "gh pr merge failed for PR #$Pr"
}

Write-Output "PR #$Pr merged with method: $MergeMethod"
if ($DeleteBranch) {
  Write-Output "Branch delete requested after merge."
}
