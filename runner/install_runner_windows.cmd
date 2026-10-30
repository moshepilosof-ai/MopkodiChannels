@echo off
REM Installs a GitHub Actions self-hosted runner on this Windows computer for the MopkodiChannels repo,
REM as a Windows service that starts with the computer. The refresh workflows then run HERE (Israeli address)
REM instead of on GitHub's servers in the US. The TV keeps reading the files from GitHub.
REM
REM Usage:  install_runner_windows.cmd <registration token>
REM The token comes from GitHub: repo Settings -> Actions -> Runners -> New self-hosted runner (valid one hour).
REM Needs: Git for Windows (git.exe in PATH). Python is downloaded by the workflow itself.
REM Installed under C:ctions-runner-mopkodi: the service account (NETWORK SERVICE) cannot read a user profile folder.
setlocal
if "%~1"=="" (
    echo Usage: %~nx0 ^<registration token^>
    exit /b 1
)
set "REPO_URL=https://github.com/moshepilosof-ai/MopkodiChannels"
set "RUNNER_VER=2.338.2"
set "DIR=%USERPROFILE%\actions-runner-mopkodi"
if not exist "%DIR%" mkdir "%DIR%"
cd /d "%DIR%"
if not exist run.cmd (
    echo Downloading runner %RUNNER_VER%...
    powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = 'Tls12'; Invoke-WebRequest -Uri 'https://github.com/actions/runner/releases/download/v%RUNNER_VER%/actions-runner-win-x64-%RUNNER_VER%.zip' -OutFile runner.zip"
    if errorlevel 1 ( echo download failed & exit /b 1 )
    powershell -NoProfile -Command "Expand-Archive -Path runner.zip -DestinationPath . -Force"
    del runner.zip
)
echo Registering with %REPO_URL% ...
call config.cmd --url %REPO_URL% --token %~1 --name "%COMPUTERNAME%-israel" --labels israel --unattended --replace --runasservice
if errorlevel 1 ( echo registration failed & exit /b 1 )
echo.
echo Runner installed as a Windows service. Check: GitHub repo -> Settings -> Actions -> Runners (should be "Idle").
echo To remove later:  cd "%DIR%" ^&^& config.cmd remove --token ^<removal token^>
endlocal
