@echo off
REM Quick Test Runner - הרצת בדיקות מהירה
REM ========================================

echo ============================================================
echo    AppsFlyerAgent - Quick Test Runner
echo ============================================================
echo.

REM Change to parent directory (AppsFlyerAgent)
cd /d "%~dp0.."

echo [1/3] Running Simple Demo...
echo ------------------------------------------------------------
python tests\simple_demo.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Demo failed!
    pause
    exit /b 1
)

echo.
echo.
echo [2/3] Running Pytest - JSON Utils...
echo ------------------------------------------------------------
python -m pytest tests\test_json_utils.py -v
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: JSON tests failed!
    pause
    exit /b 1
)

echo.
echo.
echo [3/3] Running Pytest - All Standalone Tests...
echo ------------------------------------------------------------
python -m pytest tests\test_standalone.py -v
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Standalone tests failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    All Tests Completed Successfully! ✓
echo ============================================================
echo.
echo Summary:
echo   - Simple Demo: PASSED
echo   - JSON Utils (5 tests): PASSED
echo   - Standalone Tests (15 tests): PASSED
echo   - Total: 20 tests PASSED
echo.
echo For detailed testing guide, see:
echo   - TESTING_SUMMARY.md
echo   - tests\README.md
echo.
pause
