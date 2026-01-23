@echo off
REM EBS Design Document Analysis and Merge Tool - Setup Verification

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
for %%I in ("%SCRIPT_DIR%") do set PROJECT_ROOT=%%~dpI
set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%

REM Change to project root
cd /d "%PROJECT_ROOT%"

echo ============================================================
echo EBS Merge Tool - Setup Verification
echo ============================================================
echo.

set ERROR_COUNT=0

REM 1. Check Python version
echo [1/7] Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo   [FAIL] Python is not installed
    set /a ERROR_COUNT+=1
) else (
    echo   [OK] Python is installed
)
echo.

REM 2. Check dependencies
echo [2/7] Checking dependencies...
python -c "import pandas" >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] pandas is not installed
    set /a ERROR_COUNT+=1
) else (
    echo   [OK] pandas
)

python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] openpyxl is not installed
    set /a ERROR_COUNT+=1
) else (
    echo   [OK] openpyxl
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] requests is not installed
    set /a ERROR_COUNT+=1
) else (
    echo   [OK] requests
)

python -c "import dotenv" >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] python-dotenv is not installed
    set /a ERROR_COUNT+=1
) else (
    echo   [OK] python-dotenv
)
echo.

REM 3. Check .env file
echo [3/7] Checking .env file...
if exist ".env" (
    echo   [OK] .env file exists
) else (
    echo   [FAIL] .env file not found
    set /a ERROR_COUNT+=1
    if exist ".env.example" (
        echo   INFO: Can be created from .env.example
    )
)
echo.

REM 4. Check input folder
echo [4/7] Checking input folder...
if exist "input" (
    echo   [OK] input folder exists
    
    REM Count Excel files
    set FILE_COUNT=0
    for %%f in (input\*.xlsx input\*.xls) do set /a FILE_COUNT+=1
    if !FILE_COUNT! gtr 0 (
        echo   [OK] Found !FILE_COUNT! Excel file(s)
    ) else (
        echo   [WARN] No Excel files found
    )
) else (
    echo   [WARN] input folder does not exist (will be created automatically)
)
echo.

REM 5. Check output folder
echo [5/7] Checking output folder...
if exist "output" (
    echo   [OK] output folder exists
) else (
    echo   [INFO] output folder does not exist (will be created automatically)
)
echo.

REM 6. Check template folder
echo [6/7] Checking template folder...
if exist "template" (
    echo   [OK] template folder exists
    if exist "template\IF_Template.xlsm" (
        echo   [OK] IF_Template.xlsm exists
    ) else (
        echo   [FAIL] IF_Template.xlsm not found
        set /a ERROR_COUNT+=1
    )
) else (
    echo   [FAIL] template folder not found
    set /a ERROR_COUNT+=1
)
echo.

REM 7. Check module imports
echo [7/7] Checking module imports...
python -c "from ebs_merger.cli import EBSMergerCLI; from ebs_merger.ai_generator import AIGenerator; from ebs_merger.ai_classifier import AIClassifier" >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Failed to import modules
    set /a ERROR_COUNT+=1
) else (
    echo   [OK] All modules imported successfully
)
echo.

REM Summary
echo ============================================================
echo Verification Summary
echo ============================================================
if %ERROR_COUNT% equ 0 (
    echo [OK] All checks passed!
    echo.
    echo Ready to run the tool
    echo.
    echo How to run:
    echo   run_merge.bat
) else (
    echo [FAIL] Found %ERROR_COUNT% issue(s)
    echo.
    echo Please fix the issues and run again
    echo.
    echo How to fix:
    echo   1. Install dependencies:
    echo      pip install -r requirements.txt
    echo.
    echo   2. Create .env file:
    echo      copy .env.example .env
    echo      notepad .env
    echo.
    echo   3. Place Excel files:
    echo      Place Excel files in input folder
)
echo ============================================================
echo.

REM Run detailed verification
echo Run detailed verification? (Y/N)
set /p run_detailed=
if /i "%run_detailed%"=="Y" (
    echo.
    echo Running detailed verification...
    python verify_config.py
)

pause
