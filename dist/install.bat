@echo off
title نصب Control System Manager

echo.
echo ============================================================
echo    Control System Manager - نصب
echo ============================================================
echo.

REM ساخت پوشه داده
set DATA_DIR=D:\BMS Projects\IO_List_Generator
if exist "D:\" (
    if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
    if not exist "%DATA_DIR%\Backups" mkdir "%DATA_DIR%\Backups"
    if not exist "%DATA_DIR%\config" mkdir "%DATA_DIR%\config"
    if not exist "%DATA_DIR%\logs" mkdir "%DATA_DIR%\logs"
    if not exist "%DATA_DIR%\Attachments" mkdir "%DATA_DIR%\Attachments"
    echo ✅ پوشه‌های داده ساخته شد
)

REM ساخت میان‌بر دسکتاپ
set SCRIPT="%TEMP%\%RANDOM%.vbs"
set EXE_PATH=%~dp0ControlSystemManager.exe

echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\Control System Manager.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%EXE_PATH%" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

echo ✅ میان‌بر دسکتاپ ساخته شد
echo.
echo ============================================================
echo    نصب کامل شد!
echo ============================================================
pause