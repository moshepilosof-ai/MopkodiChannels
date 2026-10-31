@echo off
REM Installs MopPlusServer.exe on this computer so it runs all the time, for the TV app on the home network:
REM   - copies the exe to C:\MopPlus (the addon and its data are downloaded there, nothing hidden)
REM   - opens TCP port 27455 in the Windows firewall (home network only)
REM   - registers a scheduled task that starts the server at boot (as SYSTEM, no login needed) and starts it now
REM Run as administrator, from the folder that holds MopPlusServer.exe (or pass its path as the first argument).
setlocal
set "SRC=%~1"
if "%SRC%"=="" set "SRC=%~dp0MopPlusServer.exe"
if not exist "%SRC%" (
    echo MopPlusServer.exe not found: %SRC%
    exit /b 1
)
set "DIR=C:\MopPlus"
if not exist "%DIR%" mkdir "%DIR%"
schtasks /end /tn MopPlusServer >nul 2>&1
taskkill /IM MopPlusServer.exe /F >nul 2>&1
copy /Y "%SRC%" "%DIR%\MopPlusServer.exe" >nul || (echo copy failed & exit /b 1)
netsh advfirewall firewall delete rule name="MopPlusServer" >nul 2>&1
netsh advfirewall firewall add rule name="MopPlusServer" dir=in action=allow protocol=TCP localport=27455 profile=private,domain >nul
schtasks /create /tn MopPlusServer /tr "\"%DIR%\MopPlusServer.exe\"" /sc onstart /ru SYSTEM /rl highest /f >nul || (echo task creation failed & exit /b 1)
schtasks /run /tn MopPlusServer >nul
echo.
echo MopPlusServer installed in %DIR% and started. Log: %DIR%\MopPlusServer.log
echo Check from another computer:  http://%COMPUTERNAME%:27455/api/info
echo To remove:  schtasks /delete /tn MopPlusServer /f  ^&^&  netsh advfirewall firewall delete rule name="MopPlusServer"
endlocal
