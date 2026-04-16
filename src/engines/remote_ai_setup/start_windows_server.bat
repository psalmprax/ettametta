@echo off
REM ettametta Windows Laptop AI Server Startup Script

echo 🚀 Starting ettametta Laptop AI Server...
echo.

REM Check if conda is available
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Conda not found. Please install Miniconda first.
    echo Download from: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

REM Check if environment exists
conda env list | findstr "ettametta-ai" >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Conda environment 'ettametta-ai' not found.
    echo Run: conda create -n ettametta-ai python=3.11
    pause
    exit /b 1
)

REM Activate environment
echo 📦 Activating conda environment...
call conda activate ettametta-ai
if %errorlevel% neq 0 (
    echo ❌ Failed to activate conda environment
    pause
    exit /b 1
)

REM Set environment variables
echo ⚙️ Setting environment variables...
set HF_HOME=%USERPROFILE%\.hf_cache
set PYTHONPATH=%~dp0;%PYTHONPATH%

REM Check for ngrok token
if "%NGROK_AUTH_TOKEN%"=="" (
    echo ⚠️ NGROK_AUTH_TOKEN not set. Get one from https://ngrok.com
    echo Set it with: set NGROK_AUTH_TOKEN=your_token_here
    echo Continuing without ngrok...
)

REM Create outputs directory
if not exist "outputs" mkdir outputs

REM Start the server
echo 🎬 Starting AI server on port 8122...
python windows_laptop_server.py

REM Keep window open on error
pause