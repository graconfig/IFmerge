@echo off
REM EBS Design Document Analysis and Merge Tool - Quick Start

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
for %%I in ("%SCRIPT_DIR%") do set PROJECT_ROOT=%%~dpI
set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%

REM Change to project root
cd /d "%PROJECT_ROOT%"

echo ============================================================
echo EBS Merge Tool - Quick Start
echo ============================================================
echo.

REM Step 1: Install dependencies
echo [Step 1/3] Installing dependencies
echo.
echo Install dependencies? (Y/N)
echo (Select N if already installed)
set /p install_deps=
if /i "%install_deps%"=="Y" (
    echo.
    echo Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Installation failed
        pause
        exit /b 1
    )
    echo.
    echo Installation completed
)
echo.

REM Step 2: Create configuration file
echo [Step 2/3] Creating configuration file
echo.
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env file...
        copy .env.example .env >nul
        echo.
        echo Created .env file
        echo.
        echo IMPORTANT: Please enter your SAP AI Core credentials
        echo.
        echo Open .env file? (Y/N)
        set /p open_env=
        if /i "%open_env%"=="Y" (
            notepad .env
        )
    ) else (
        echo ERROR: .env.example file not found
        pause
        exit /b 1
    )
) else (
    echo .env file already exists
    echo.
    echo Edit .env file? (Y/N)
    set /p edit_env=
    if /i "%edit_env%"=="Y" (
        notepad .env
    )
)
echo.

REM Step 3: Place Excel files
echo [Step 3/3] Placing Excel files
echo.
if not exist "input" (
    echo Creating input folder...
    mkdir input
)

dir /b input\*.xlsx input\*.xls >nul 2>&1
if errorlevel 1 (
    echo Please place Excel files in the input folder
    echo.
    echo Open input folder? (Y/N)
    set /p open_input=
    if /i "%open_input%"=="Y" (
        explorer input
        echo.
        echo Press Enter after placing Excel files
        pause >nul
    ) else (
        echo.
        echo Please place Excel files and run run_merge.bat
        pause
        exit /b 0
    )
) else (
    echo Excel files found
)
echo.

REM Verify configuration
echo ============================================================
echo Verifying configuration...
echo ============================================================
echo.

python -c "import sys; sys.exit(0 if __import__('pathlib').Path('.env').exists() else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: There may be issues with the configuration
    echo.
    echo Continue anyway? (Y/N)
    set /p continue_anyway=
    if /i not "%continue_anyway%"=="Y" (
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo Setup completed!
echo ============================================================
echo.
echo Run the tool now? (Y/N)
set /p run_now=
if /i "%run_now%"=="Y" (
    echo.
    call "%SCRIPT_DIR%\run_merge.bat"
) else (
    echo.
    echo To run the tool, execute:
    echo   run_merge.bat
    echo.
    echo Or:
    echo   python -m ebs_merger
    echo.
    pause
)
