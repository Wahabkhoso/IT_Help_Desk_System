@echo off
setlocal

echo ============================================
echo  IT Help Desk - Build Windows .exe
echo ============================================
echo.

REM Step 1: Confirm we're in the right folder
if not exist main.py (
    echo [ERROR] main.py not found in this folder.
    echo Make sure build.bat is inside the IT_Help_Desk folder
    echo ^(the same folder that has main.py, ui, services, etc.^)
    echo.
    pause
    exit /b 1
)

REM Step 2: Confirm Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH.
    echo Install Python from https://python.org and make sure to check
    echo "Add Python to PATH" during installation, then try again.
    echo.
    pause
    exit /b 1
)
echo [OK] Python found:
python --version
echo.

REM Step 3: Install/upgrade PyInstaller (using "python -m pip" is more
REM reliable on Windows than a bare "pip" command, which can point to the
REM wrong Python install or not be on PATH at all).
echo Installing/updating PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller. See the message above.
    echo.
    pause
    exit /b 1
)
echo.

REM Step 4: Build (using "python -m PyInstaller" for the same PATH reason)
echo Building IT_Help_Desk.exe ...
echo This can take 1-3 minutes - please wait for it to finish.
echo.
python -m PyInstaller --onefile --windowed --name "IT_Help_Desk" --clean main.py

REM Step 5: Verify the .exe actually got created
if exist "dist\IT_Help_Desk.exe" (
    echo.
    echo ============================================
    echo  SUCCESS! Your app is at: dist\IT_Help_Desk.exe
    echo ============================================
) else (
    echo.
    echo ============================================
    echo  [ERROR] Build finished but dist\IT_Help_Desk.exe
    echo  was not created. Scroll up to find the error message
    echo  above ^(it's usually near a line saying "ERROR:" or
    echo  a Python traceback^), and share that with support.
    echo ============================================
)

echo.
pause
