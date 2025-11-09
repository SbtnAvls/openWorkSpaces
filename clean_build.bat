@echo off
echo Cleaning build directories...
echo.

REM Kill any running processes
echo Stopping any running WorkspaceManager processes...
taskkill /F /IM WorkspaceManager.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Try to remove directories
echo Removing build artifacts...
if exist "build" (
    rmdir /s /q "build" 2>nul
    if exist "build" (
        echo WARNING: Could not remove build/ - May be in use
    ) else (
        echo Removed build/
    )
)

if exist "dist" (
    rmdir /s /q "dist" 2>nul
    if exist "dist" (
        echo WARNING: Could not remove dist/ - May be in use
        echo Please close any Windows Explorer windows and try again
    ) else (
        echo Removed dist/
    )
)

if exist "version_info.txt" (
    del "version_info.txt" 2>nul
    echo Removed version_info.txt
)

echo.
echo Done!
echo.
pause
