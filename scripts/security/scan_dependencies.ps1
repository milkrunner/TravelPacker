# Dependency Security Scanning Script for Windows (PowerShell)
# Scans Python dependencies for known vulnerabilities using pip-audit

param(
    [switch]$Install,
    [switch]$Fix,
    [switch]$Json,
    [switch]$Strict,
    [string]$Output = "security-scan-report.txt"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NikNotes Dependency Security Scanner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if pip-audit is installed
$pipAuditInstalled = $false
try {
    $null = pip-audit --version 2>$null
    $pipAuditInstalled = $true
} catch {
    $pipAuditInstalled = $false
}

if (-not $pipAuditInstalled) {
    if ($Install) {
        Write-Host "Installing pip-audit..." -ForegroundColor Yellow
        pip install pip-audit
        Write-Host "pip-audit installed successfully!" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "ERROR: pip-audit is not installed." -ForegroundColor Red
        Write-Host "Run this script with -Install flag to install it:" -ForegroundColor Yellow
        Write-Host "  .\scripts\scan_dependencies.ps1 -Install" -ForegroundColor White
        Write-Host ""
        Write-Host "Or install manually:" -ForegroundColor Yellow
        Write-Host "  pip install pip-audit" -ForegroundColor White
        exit 1
    }
}

Write-Host "Starting dependency scan..." -ForegroundColor Cyan
Write-Host "Scan date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# Build pip-audit command
$command = "pip-audit"
$arguments = @("--desc")

if ($Json) {
    $arguments += "--format", "json"
    if ($Output -eq "security-scan-report.txt") {
        $Output = "security-scan-report.json"
    }
    $arguments += "--output", $Output
} elseif ($Output -ne "security-scan-report.txt") {
    # For text output, we'll capture and save manually
    $arguments += "--format", "columns"
}

if ($Fix) {
    Write-Host "Auto-fix mode enabled - will attempt to upgrade vulnerable packages" -ForegroundColor Yellow
    $arguments += "--fix"
}

if ($Strict) {
    Write-Host "Strict mode enabled - will fail on any vulnerability" -ForegroundColor Yellow
}

# Run pip-audit
Write-Host "Running: pip-audit $($arguments -join ' ')" -ForegroundColor Gray
Write-Host ""

try {
    if ($Json) {
        # JSON output goes to file
        & pip-audit $arguments
        Write-Host ""
        Write-Host "JSON report saved to: $Output" -ForegroundColor Green
    } else {
        # Capture output for both display and file
        $scanOutput = & pip-audit $arguments 2>&1 | Out-String
        Write-Host $scanOutput
        
        # Save to file
        $scanOutput | Out-File -FilePath $Output -Encoding UTF8
        Write-Host ""
        Write-Host "Report saved to: $Output" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Scan completed successfully!" -ForegroundColor Green
    
    if ($Strict) {
        Write-Host ""
        Write-Host "Running strict check..." -ForegroundColor Yellow
        & pip-audit --strict --require-hashes=false
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "No vulnerabilities found!" -ForegroundColor Green
        } else {
            Write-Host "Vulnerabilities detected! See report above." -ForegroundColor Red
            exit 1
        }
    }
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Scan failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Scan Summary:" -ForegroundColor Cyan
Write-Host "  - Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host "  - Report: $Output" -ForegroundColor White
Write-Host "  - Mode: $(if ($Fix) { 'Auto-fix' } elseif ($Strict) { 'Strict' } else { 'Scan only' })" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Display next steps
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review the report above or in $Output" -ForegroundColor White
Write-Host "  2. Update vulnerable packages: pip install --upgrade <package>" -ForegroundColor White
Write-Host "  3. Run again with -Fix to auto-upgrade: .\scripts\scan_dependencies.ps1 -Fix" -ForegroundColor White
Write-Host "  4. Add to CI/CD: See .github/workflows/security-scan.yml" -ForegroundColor White
Write-Host ""
