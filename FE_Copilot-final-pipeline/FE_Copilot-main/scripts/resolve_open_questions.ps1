param(
    [string[]]$DocPaths = @(
        "spec_repo/01_Requirements_and_Domain_Foundation.md",
        "spec_repo/02_Domain_and_Data_Model.md"
    ),
    [string]$DecisionFile = "sources/decisions.md",
    [ValidatePattern("^0[1-8]$")]
    [string]$Stage,
    [switch]$RequireResolution
)

$ErrorActionPreference = "Stop"

function Get-NextDecisionId {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return "DEC-001"
    }

    $content = Get-Content -Path $Path -Raw
    $matches = [regex]::Matches($content, "##\s+DEC-(\d{3})")
    if ($matches.Count -eq 0) {
        return "DEC-001"
    }

    $max = 0
    foreach ($m in $matches) {
        $val = [int]$m.Groups[1].Value
        if ($val -gt $max) { $max = $val }
    }

    return ("DEC-{0:D3}" -f ($max + 1))
}

function Ensure-DecisionFile {
    param([string]$Path)

    if (Test-Path $Path) {
        return
    }

    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    @'
# Decision Register

This file stores approved decisions for unresolved items surfaced during document generation.
Treat this as a source-of-truth input for targeted regeneration.

## Usage Rules

- Do not edit generated files in `spec_repo/` by hand.
- Record decisions here first.
- Re-run the affected stage agent so the generated docs consume the decision.
- Keep IDs stable and append new decisions instead of rewriting history.
'@ | Set-Content -Path $Path -Encoding utf8
}

function Collect-OpenQuestions {
    param([string[]]$Paths)

    $items = @()
    $seen = @{}

    foreach ($path in $Paths) {
        if (-not (Test-Path $path)) {
            continue
        }

        $lines = Get-Content -Path $path
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match "^\s*\|\s*Open Question\s*\|") {
                $cells = $lines[$i].Trim().Trim("|").Split("|")
                $question = if ($cells.Count -gt 1) { $cells[1].Trim() } else { $lines[$i].Trim() }
                $normalized = ($question -replace "\s+", " ").ToLowerInvariant()
                $oqMatch = [regex]::Match($lines[$i], "\[(OQ-\d{2,3})\]")
                $key = if ($oqMatch.Success) { $oqMatch.Groups[1].Value } else { $normalized }
                if ($seen.ContainsKey($key)) {
                    continue
                }
                $seen[$key] = $true
                $items += [pscustomobject]@{
                    File = $path
                    Line = $i + 1
                    Text = $lines[$i].Trim()
                }
            }
        }
    }

    return $items
}

Ensure-DecisionFile -Path $DecisionFile
$questions = Collect-OpenQuestions -Paths $DocPaths

if ($questions.Count -eq 0) {
    Write-Host "No Open Question entries found in selected docs." -ForegroundColor Green
    exit 0
}

Write-Host "Found $($questions.Count) Open Question entries." -ForegroundColor Yellow
Write-Host "Decision file: $DecisionFile"
Write-Host ""

$decide = New-Object System.Management.Automation.Host.ChoiceDescription "&Decide now", "Record an approved decision now"
$defer = New-Object System.Management.Automation.Host.ChoiceDescription "&Defer", "Keep this Open Question unresolved for now"
$stop  = New-Object System.Management.Automation.Host.ChoiceDescription "&Stop", "Stop and finish"
if ($RequireResolution) {
    $choices = [System.Management.Automation.Host.ChoiceDescription[]]@($decide, $stop)
    $stopIndex = 1
} else {
    $choices = [System.Management.Automation.Host.ChoiceDescription[]]@($decide, $defer, $stop)
    $stopIndex = 2
}

$recorded = 0
$stopped = $false

# Collect all answers in memory first, write all at once, then exit once.
# If the operator stops mid-list, nothing partial has been written yet, so
# remaining/interrupted questions do not trigger a spurious re-analysis pass.
$pendingDecisions = @()

for ($idx = 0; $idx -lt $questions.Count; $idx++) {
    $q = $questions[$idx]

    Write-Host "[$($idx + 1)/$($questions.Count)] $($q.File):$($q.Line)" -ForegroundColor Cyan
    Write-Host $q.Text

    $selection = $host.UI.PromptForChoice(
        "Open Question Decision",
        "Choose an action for this item.",
        $choices,
        1
    )

    if ($selection -eq $stopIndex) {
        $stopped = $true
        break
    }

    if (-not $RequireResolution -and $selection -eq 1) {
        Write-Host "Deferred." -ForegroundColor DarkYellow
        Write-Host ""
        continue
    }

    do {
        $decision = Read-Host "Decision (approved statement)"
    } while ([string]::IsNullOrWhiteSpace($decision))

    do {
        $sourceBasis = Read-Host "Source basis (who/what approved this)"
    } while ([string]::IsNullOrWhiteSpace($sourceBasis))

    $appliesTo = Read-Host "Applies to (e.g., stage 02 enum values)"
    if ([string]::IsNullOrWhiteSpace($appliesTo)) {
        $appliesTo = "Open Question in generated stage document"
    }

    $notes = Read-Host "Optional notes (press Enter to skip)"
    if ([string]::IsNullOrWhiteSpace($notes)) {
        $notes = "-"
    }

    # Queue in memory only - not written to disk yet.
    $pendingDecisions += [pscustomobject]@{
        Question    = $q.Text
        Decision    = $decision
        AppliesTo   = $appliesTo
        SourceBasis = $sourceBasis
        Notes       = $notes
        File        = $q.File
        Line        = $q.Line
    }

    Write-Host "Queued (not yet written)." -ForegroundColor DarkCyan
    Write-Host ""
}

# Write ALL queued decisions at once, after the loop ends (or is stopped).
foreach ($pending in $pendingDecisions) {
    $decisionId = Get-NextDecisionId -Path $DecisionFile
    $date = Get-Date -Format "yyyy-MM-dd"

    Add-Content -Path $DecisionFile -Value ""
    Add-Content -Path $DecisionFile -Value "## $decisionId ($date) - Approved"
    Add-Content -Path $DecisionFile -Value "- Question: $($pending.Question)"
    Add-Content -Path $DecisionFile -Value "- Decision: $($pending.Decision)"
    Add-Content -Path $DecisionFile -Value "- Applies to: $($pending.AppliesTo)"
    if (-not [string]::IsNullOrWhiteSpace($Stage)) {
        Add-Content -Path $DecisionFile -Value "- Applies to stages: $Stage"
    }
    Add-Content -Path $DecisionFile -Value "- Source basis: $($pending.SourceBasis)"
    Add-Content -Path $DecisionFile -Value "- References: $($pending.File):$($pending.Line)"
    Add-Content -Path $DecisionFile -Value "- Notes: $($pending.Notes)"

    $recorded++

    Write-Host "Written $decisionId" -ForegroundColor Green
}

Write-Host ""
Write-Host "Decision capture complete. Recorded: $recorded" -ForegroundColor Green
if ($stopped) {
    Write-Host "Stopped by operator. No further stages will run." -ForegroundColor Yellow
    exit 20
}

if ($recorded -gt 0) {
    Write-Host "The current stage must regenerate from $DecisionFile." -ForegroundColor Yellow
    exit 10
}

Write-Host "No decisions recorded. Deferred questions remain in the generated document."
exit 0
