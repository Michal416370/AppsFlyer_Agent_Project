# Quick Test Runner - PowerShell
# הרצת בדיקות מהירה

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   AppsFlyerAgent - Quick Test Runner" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Change to parent directory (AppsFlyerAgent)
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "[1/3] Running Simple Demo..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"
python tests\simple_demo.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Demo failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host ""
Write-Host "[2/3] Running Pytest - JSON Utils..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"
python -m pytest tests\test_json_utils.py -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: JSON tests failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host ""
Write-Host "[3/3] Running Pytest - All Standalone Tests..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"
python -m pytest tests\test_standalone.py -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Standalone tests failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   All Tests Completed Successfully! " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  - Simple Demo: PASSED" -ForegroundColor Green
Write-Host "  - JSON Utils (5 tests): PASSED" -ForegroundColor Green
Write-Host "  - Standalone Tests (15 tests): PASSED" -ForegroundColor Green
Write-Host "  - Total: 20 tests PASSED" -ForegroundColor Green
Write-Host ""
Write-Host "For detailed testing guide, see:" -ForegroundColor Cyan
Write-Host "  - TESTING_SUMMARY.md"
Write-Host "  - tests\README.md"
Write-Host ""
Read-Host "Press Enter to exit"

