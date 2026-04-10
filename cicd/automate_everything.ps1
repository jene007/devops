param(
    [string]$Repository = "jene007/devops",
    [string]$BaseBranch = "master",
    [string]$HeadBranch = "feature/rubric-full-marks",
    [string]$WorkflowName = "JARVIS DevOps CI/CD",
    [string]$PrTitle = "feat: rubric-complete devops automation",
    [string]$PrBodyFile = "cicd/PR_DESCRIPTION.md",
    [switch]$SkipSecrets,
    [switch]$SkipMerge,
    [switch]$SkipPush,
    [int]$RunDiscoveryRetries = 12,
    [int]$RunDiscoveryDelaySeconds = 10
)

$ErrorActionPreference = "Stop"

function Assert-Tool {
    param([string]$ToolName, [string]$Hint)
    if (-not (Get-Command $ToolName -ErrorAction SilentlyContinue)) {
        throw "Missing required command '$ToolName'. $Hint"
    }
}

function Get-RequiredEnvironmentValue {
    param([string]$VariableName)
    $value = [Environment]::GetEnvironmentVariable($VariableName)
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Missing required environment variable: $VariableName"
    }
    return $value
}

function Get-RepositoryFromRemote {
    $originUrl = git remote get-url origin
    if ($originUrl -match "github.com[:/](?<repo>[^/]+/[^/.]+)") {
        return $Matches.repo
    }
    return $null
}

function Wait-ForRun {
    param(
        [string]$Repo,
        [string]$Workflow,
        [string]$Branch,
        [string]$RunType,
        [int]$Retries,
        [int]$DelaySeconds
    )

    for ($i = 1; $i -le $Retries; $i++) {
        $json = gh run list --repo $Repo --workflow $Workflow --branch $Branch --event $RunType --limit 1 --json databaseId,url,status,conclusion,headBranch
        $runs = $json | ConvertFrom-Json
        if ($runs -and $runs.Count -gt 0) {
            return $runs[0]
        }
        Write-Host "Waiting for $RunType run to appear (attempt $i/$Retries)..."
        Start-Sleep -Seconds $DelaySeconds
    }

    throw "No run found for workflow '$Workflow' on branch '$Branch' and event '$RunType'."
}

Assert-Tool -ToolName "git" -Hint "Install Git and ensure it is on PATH."
Assert-Tool -ToolName "gh" -Hint "Install GitHub CLI from https://cli.github.com/ and ensure it is on PATH."

gh auth status 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

if ($Repository -eq "") {
    $Repository = Get-RepositoryFromRemote
    if (-not $Repository) {
        throw "Repository not provided and could not infer from git remote."
    }
}

$currentBranch = git branch --show-current
if ($currentBranch -ne $HeadBranch) {
    Write-Host "Checking out head branch '$HeadBranch'..."
    git checkout $HeadBranch
}

if (-not $SkipPush) {
    Write-Host "Pushing '$HeadBranch' to origin..."
    git push -u origin $HeadBranch
}

if (-not $SkipSecrets) {
    Write-Host "Setting required GitHub Actions secrets in $Repository..."
    $secretNames = @(
        "DOCKERHUB_USERNAME",
        "DOCKERHUB_TOKEN",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION",
        "KUBE_CONFIG_DATA"
    )

    foreach ($secret in $secretNames) {
        $secretValue = Get-RequiredEnvironmentValue -VariableName $secret
        $secretValue | gh secret set $secret --repo $Repository --body -
        Write-Host "Secret set: $secret"
    }
}

$prNumber = $null
$existingPrJson = gh pr list --repo $Repository --head $HeadBranch --base $BaseBranch --state open --limit 1 --json number,url
$existingPr = $existingPrJson | ConvertFrom-Json
if ($existingPr -and $existingPr.Count -gt 0) {
    $prNumber = $existingPr[0].number
    Write-Host "Using existing PR #$prNumber -> $($existingPr[0].url)"
}
else {
    Write-Host "Creating pull request from '$HeadBranch' to '$BaseBranch'..."
    if (Test-Path $PrBodyFile) {
        gh pr create --repo $Repository --base $BaseBranch --head $HeadBranch --title $PrTitle --body-file $PrBodyFile
    }
    else {
        gh pr create --repo $Repository --base $BaseBranch --head $HeadBranch --title $PrTitle --body "Automated PR created by cicd/automate_everything.ps1"
    }

    $prView = gh pr list --repo $Repository --head $HeadBranch --base $BaseBranch --state open --limit 1 --json number,url | ConvertFrom-Json
    if (-not $prView -or $prView.Count -eq 0) {
        throw "PR creation was attempted but no open PR was found."
    }
    $prNumber = $prView[0].number
    Write-Host "Created PR #$prNumber -> $($prView[0].url)"
}

Write-Host "Waiting for required PR checks to finish..."
gh pr checks $prNumber --repo $Repository --watch --required
if ($LASTEXITCODE -ne 0) {
    throw "PR checks failed for PR #$prNumber"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceDir = Join-Path "cicd/evidence" $timestamp
New-Item -Path $evidenceDir -ItemType Directory -Force | Out-Null

$prRun = Wait-ForRun -Repo $Repository -Workflow $WorkflowName -Branch $HeadBranch -RunType "pull_request" -Retries $RunDiscoveryRetries -DelaySeconds $RunDiscoveryDelaySeconds
$prRunId = $prRun.databaseId
Write-Host "Capturing PR run logs from run ID $prRunId..."
gh run view $prRunId --repo $Repository --log > (Join-Path $evidenceDir "pr-run.log")

if (-not $SkipMerge) {
    Write-Host "Merging PR #$prNumber into '$BaseBranch'..."
    gh pr merge $prNumber --repo $Repository --squash --delete-branch
}

$mainRun = Wait-ForRun -Repo $Repository -Workflow $WorkflowName -Branch $BaseBranch -RunType "push" -Retries $RunDiscoveryRetries -DelaySeconds $RunDiscoveryDelaySeconds
$mainRunId = $mainRun.databaseId
Write-Host "Waiting for main-branch deploy run ID $mainRunId to complete..."
gh run watch $mainRunId --repo $Repository --exit-status
if ($LASTEXITCODE -ne 0) {
    throw "Main-branch workflow run failed: $mainRunId"
}

Write-Host "Capturing main-branch run logs from run ID $mainRunId..."
gh run view $mainRunId --repo $Repository --log > (Join-Path $evidenceDir "master-run.log")

$summaryPath = Join-Path $evidenceDir "summary.md"
@(
    "# Automated Evidence Summary",
    "",
    "- Repository: $Repository",
    "- Base branch: $BaseBranch",
    "- Head branch: $HeadBranch",
    "- Pull request: #$prNumber",
    "- PR run URL: $($prRun.url)",
    "- Main run URL: $($mainRun.url)",
    "- PR logs: pr-run.log",
    "- Main logs: master-run.log",
    "- Rubric file: cicd/RUBRIC_EVIDENCE.md"
) | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "Automation complete."
Write-Host "Evidence directory: $evidenceDir"
