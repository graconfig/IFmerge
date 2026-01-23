@echo off
setlocal enabledelayedexpansion
REM EBS Design Document Analysis and Merge Tool Execution Script

REM Get absolute path of script directory
set "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash
if "!SCRIPT_DIR:~-1!"=="\" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"

REM Get parent directory (project root)
for %%I in ("!SCRIPT_DIR!") do set "PROJECT_ROOT=%%~dpI"
REM Remove trailing backslash  
if "!PROJECT_ROOT:~-1!"=="\" set "PROJECT_ROOT=!PROJECT_ROOT:~0,-1!"

REM Change to project root
cd /d "!PROJECT_ROOT!"

echo ============================================================
echo EBS Merge Tool
echo ============================================================
echo.
echo Project: !PROJECT_ROOT!
echo.

REM Verify we are in the correct directory
if not exist "!PROJECT_ROOT!\ebs_merger" (
    echo ERROR: Cannot find ebs_merger folder
    echo.
    pause
    exit /b 1
)

echo Checking configuration...
echo.

REM Check .env file (create if needed)
if not exist "!PROJECT_ROOT!\.env" (
    if exist "!PROJECT_ROOT!\.env.example" (
        echo .env file not found. Creating from .env.example...
        copy "!PROJECT_ROOT!\.env.example" "!PROJECT_ROOT!\.env" >nul
        echo.
        echo IMPORTANT: Opening .env file for configuration
        echo Please enter your SAP AI Core credentials and save the file
        echo.
        timeout /t 2 >nul
        notepad "!PROJECT_ROOT!\.env"
        echo.
    ) else (
        echo WARNING: .env file not found
        echo.
    )
)

REM Check input folder
if not exist "!PROJECT_ROOT!\input" (
    mkdir "!PROJECT_ROOT!\input"
)

REM Check for Excel files
dir /b "!PROJECT_ROOT!\input\*.xlsx" "!PROJECT_ROOT!\input\*.xls" >nul 2>&1
if errorlevel 1 (
    echo WARNING: No Excel files found in input folder
    echo.
    echo Opening input folder...
    explorer "!PROJECT_ROOT!\input"
    echo.
    echo Please place Excel files in the input folder
    echo Press any key when ready...
    pause >nul
)

echo.
echo ============================================================
echo Running the tool...
echo ============================================================
echo.

REM Run the tool
python -m ebs_merger

REM Check result
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Tool execution failed
    echo ============================================================
    echo.
    echo Common issues:
    echo - Dependencies not installed: pip install -r requirements.txt
    echo - .env file not configured correctly
    echo - No Excel files in input folder
    echo - Network connection issues
    echo.
) else (
    echo.
    echo ============================================================
    echo Processing completed successfully!
    echo ============================================================
    echo.
    echo Results saved in: !PROJECT_ROOT!\output
    echo.
    echo Open output folder? (Y/N)
    set /p open_output=
    if /i "!open_output!"=="Y" (
        explorer "!PROJECT_ROOT!\output"
    )
)

echo.
pause
