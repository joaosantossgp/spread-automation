param(
  [string]$Repo,
  [string]$DefaultBranch = "main",
  [string[]]$RequiredChecks = @(),
  [switch]$ApplyBranchProtection
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command {
  param([string]$CommandName)

  if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
    throw "Required command not found in PATH: $CommandName"
  }
}

function Resolve-Repository {
  param([string]$ExplicitRepo)

  if ($ExplicitRepo) {
    return $ExplicitRepo
  }

  $repoName = gh repo view --json nameWithOwner --jq .nameWithOwner 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $repoName) {
    throw "Unable to resolve repository. Pass -Repo owner/name or run inside a gh-linked repository."
  }

  return "$repoName".Trim()
}

function Upsert-Label {
  param(
    [string]$RepoName,
    [string]$Name,
    [string]$Color,
    [string]$Description
  )

  $existing = gh label list --repo $RepoName --limit 200 |
    ForEach-Object { ($_ -split "`t")[0] } |
    Where-Object { $_ -eq $Name }

  if ($existing) {
    gh label edit $Name --repo $RepoName --color $Color --description $Description | Out-Null
  } else {
    gh label create $Name --repo $RepoName --color $Color --description $Description | Out-Null
  }
}

Require-Command -CommandName "gh"

$repoName = Resolve-Repository -ExplicitRepo $Repo

$labels = @(
  @{ Name = "kind:task"; Color = "0e8a16"; Description = "Executable task issue" },
  @{ Name = "kind:epic"; Color = "5319e7"; Description = "Planning umbrella for multiple tasks" },
  @{ Name = "status:ready"; Color = "fbca04"; Description = "Task contract is ready for execution" },
  @{ Name = "status:in-progress"; Color = "1d76db"; Description = "Work is active or PR is open" },
  @{ Name = "status:blocked"; Color = "d93f0b"; Description = "Task is blocked by dependency or decision" },
  @{ Name = "status:awaiting-consumption"; Color = "c5def5"; Description = "Child task delivered and awaits requester validation" },
  @{ Name = "status:completed"; Color = "0e8a16"; Description = "Merged and closed" },
  @{ Name = "priority:p0"; Color = "b60205"; Description = "Highest priority" },
  @{ Name = "priority:p1"; Color = "d93f0b"; Description = "High priority" },
  @{ Name = "priority:p2"; Color = "fbca04"; Description = "Normal priority" },
  @{ Name = "priority:p3"; Color = "cccccc"; Description = "Lower priority" },
  @{ Name = "area:ui"; Color = "0052cc"; Description = "Desktop UI and interaction flow" },
  @{ Name = "area:engine"; Color = "5319e7"; Description = "Runtime and orchestration" },
  @{ Name = "area:finance"; Color = "006b75"; Description = "Financial processing and mapping" },
  @{ Name = "area:data"; Color = "0e8a16"; Description = "Data ingestion and sources" },
  @{ Name = "area:governance"; Color = "bfd4f2"; Description = "Governance, CI, and repository operations" },
  @{ Name = "area:docs"; Color = "0075ca"; Description = "Documentation changes" },
  @{ Name = "risk:safe"; Color = "0e8a16"; Description = "Isolated write-set" },
  @{ Name = "risk:shared"; Color = "fbca04"; Description = "Shared or critical paths" },
  @{ Name = "risk:contract-sensitive"; Color = "b60205"; Description = "Public contract or compatibility-sensitive change" },
  @{ Name = "lane:app-ui"; Color = "0052cc"; Description = "App UI lane" },
  @{ Name = "lane:engine-finance"; Color = "006b75"; Description = "Engine finance lane" },
  @{ Name = "lane:ops-quality"; Color = "5319e7"; Description = "Ops and quality lane" }
)

foreach ($label in $labels) {
  Upsert-Label -RepoName $repoName -Name $label.Name -Color $label.Color -Description $label.Description
}

gh api --method PATCH "repos/$repoName" `
  -f allow_squash_merge=true `
  -f allow_merge_commit=false `
  -f allow_rebase_merge=false `
  -f delete_branch_on_merge=true `
  -f allow_auto_merge=false `
  -f has_issues=true `
  -f has_projects=false `
  -f has_wiki=false | Out-Null

Write-Output "Labels and repository merge settings applied to $repoName."

if (-not $ApplyBranchProtection) {
  Write-Output "Branch protection not changed. Re-run with -ApplyBranchProtection after the first PR exposes the exact check context."
  return
}

if ($RequiredChecks.Count -eq 0) {
  throw "Branch protection requires at least one check context. Pass -RequiredChecks <context>."
}

$payload = @{
  required_status_checks = @{
    strict = $true
    contexts = $RequiredChecks
  }
  enforce_admins = $false
  required_pull_request_reviews = $null
  restrictions = $null
  required_linear_history = $true
  allow_force_pushes = $false
  allow_deletions = $false
  block_creations = $false
  required_conversation_resolution = $false
  lock_branch = $false
  allow_fork_syncing = $true
} | ConvertTo-Json -Depth 6 -Compress

$tempFile = [System.IO.Path]::GetTempFileName()
try {
  Set-Content -Path $tempFile -Value $payload -Encoding ascii
  gh api --method PUT "repos/$repoName/branches/$DefaultBranch/protection" --input $tempFile | Out-Null
} finally {
  Remove-Item -Path $tempFile -ErrorAction SilentlyContinue
}

Write-Output "Branch protection applied to $DefaultBranch with checks: $($RequiredChecks -join ', ')"
