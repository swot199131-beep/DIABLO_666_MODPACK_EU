@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ================================================
echo DIABLO_666 MODPACK EU 0.6.1 - Windows build
echo ================================================

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.12 x64.
  goto :error
)
py -3.12 -m pip install --upgrade -r requirements-build.txt
if errorlevel 1 goto :error

py -3.12 tools\validate_catalog.py
if errorlevel 1 goto :error
py -3.12 -m unittest discover -s tools -p "test_*.py"
if errorlevel 1 goto :error

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
py -3.12 -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --name "DIABLO_666_MODPACK_EU" ^
  --icon "assets\diablo_icon.ico" ^
  --collect-all PIL ^
  --version-file "installer\version_info.txt" ^
  --add-data "catalog.json;." ^
  --add-data "assets;assets" ^
  --add-data "packages;packages" ^
  main.py
if errorlevel 1 goto :error

if not exist "dist\app" mkdir "dist\app"
copy /y "dist\DIABLO_666_MODPACK_EU.exe" "dist\app\DIABLO_666_MODPACK_EU.exe" >nul
if errorlevel 1 goto :error

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Inno Setup 6 not found. Install it from https://jrsoftware.org/isinfo.php
  goto :error
)
"%ISCC%" "installer\DIABLO_666_MODPACK_EU.iss"
if errorlevel 1 goto :error

certutil -hashfile "dist\installer\DIABLO_666_MODPACK_EU_Setup_v0.6.1.exe" SHA256
echo.
echo SUCCESS: dist\installer\DIABLO_666_MODPACK_EU_Setup_v0.6.1.exe
echo This build is unsigned. Verify SHA-256 before publishing.
pause
exit /b 0

:error
echo.
echo BUILD FAILED. Read the error above.
pause
exit /b 1
