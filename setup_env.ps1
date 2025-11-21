# ============================================
# Environment Variables Setup Script (PowerShell)
# ============================================
#
# This script helps set environment variables for development
#
# Usage:
#   1. Edit config.env with your real API keys
#   2. Run: .\setup_env.ps1
#   3. Or right-click > Run with PowerShell
#
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Environment Variables Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if config.env exists
if (-Not (Test-Path "config.env")) {
    Write-Host "ERROR: config.env not found!" -ForegroundColor Red
    Write-Host "Please create config.env from config.env.example:" -ForegroundColor Yellow
    Write-Host "  Copy-Item config.env.example config.env" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Load config.env
Write-Host "Loading config.env..." -ForegroundColor Green
$envVars = @{}

Get-Content "config.env" | ForEach-Object {
    $line = $_.Trim()
    # Skip comments and empty lines
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $parts = $line.Split("=", 2)
        $key = $parts[0].Trim()
        $value = $parts[1].Trim()
        $envVars[$key] = $value
    }
}

Write-Host "Found $($envVars.Count) variables" -ForegroundColor Green
Write-Host ""

# Set environment variables (User level - permanent)
Write-Host "Setting environment variables (User level)..." -ForegroundColor Yellow
Write-Host ""

$count = 0
foreach ($key in $envVars.Keys) {
    $value = $envVars[$key]

    # Skip if placeholder values
    if ($value -match "your_.*_here" -or $value -match "your-project") {
        Write-Host "  [SKIP] $key (placeholder value detected)" -ForegroundColor Gray
        continue
    }

    # Set environment variable
    [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::User)
    Write-Host "  [SET] $key" -ForegroundColor Green
    $count++
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Set $count environment variables" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Please RESTART your terminal/IDE" -ForegroundColor Yellow
Write-Host "for changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "To verify, run in new terminal:" -ForegroundColor Cyan
Write-Host "  echo `$env:GEMINI_API_KEY" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
