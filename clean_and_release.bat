@echo off
REM Complete cleanup and release script
echo ========================================
echo Windows 11 Workspace Manager
echo Clean and Release Script
echo ========================================
echo.

REM Step 1: Kill processes
echo [1/4] Stopping any running processes...
taskkill /F /IM WorkspaceManager.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo Done.
echo.

REM Step 2: Close Explorer windows on dist folder
echo [2/4] Please close any Windows Explorer windows showing the 'dist' folder
echo Press any key when ready...
pause >nul
echo.

REM Step 3: Clean directories
echo [3/4] Removing build artifacts...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "version_info.txt" del "version_info.txt" 2>nul

REM Check if cleanup was successful
if exist "dist" (
    echo.
    echo ERROR: Could not remove 'dist' folder - it is still in use
    echo.
    echo Please:
    echo   1. Close ALL Windows Explorer windows
    echo   2. Close any programs that might be using the files
    echo   3. Try running this script again
    echo.
    pause
    exit /b 1
)

echo Cleanup successful!
echo.

REM Step 4: Run release
echo [4/4] Running release build...
echo.
python release.py

echo.
echo ========================================
echo Release complete!
echo ========================================
echo.
echo Check the 'dist' folder for generated installers
echo.
pause
