# Quick Test Runner
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   AppsFlyerAgent - Test Runner" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Go to parent directory (AppsFlyerAgent)
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "[1/2] Running Demo..." -ForegroundColor Yellow
python tests\simple_demo.py
Write-Host ""

Write-Host "[2/2] Running All Tests..." -ForegroundColor Yellow
python -m pytest tests\test_json_utils.py tests\test_standalone.py -v

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Green
Write-Host "   Testing Complete!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "See TESTING_SUMMARY.md for full documentation" -ForegroundColor Cyan
