@echo off
setlocal
set "TARGET_DIR=%~dp0"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_PATH=%TARGET_DIR%start_hidden.vbs"
set "SHORTCUT=%STARTUP_DIR%\TelegramPCMonitor.lnk"

echo [1/2] Windows baslangicina kisayol olusturuluyor...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%VBS_PATH%'; $s.WorkingDirectory = '%TARGET_DIR%'; $s.Save()"

if exist "%SHORTCUT%" (
    echo [2/2] Basarili! Bilgisayar her acildiginda bot otomatik olarak arka planda calisacak.
    echo Kisayol konumu: %SHORTCUT%
) else (
    echo [HATA] Kisayol olusturulamadi.
)
pause
