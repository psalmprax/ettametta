@echo off
REM NVIDIA P4000 8GB AI Server Startup Script

echo 🚀 Starting ettametta P4000 AI Video Server...
echo 🔧 Optimized for NVIDIA Quadro P4000 8GB VRAM
echo.

REM Check if in virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo ❌ Not in virtual environment!
    echo Run: p4000_env\Scripts\activate
    pause
    exit /b 1
)

REM Set environment variables
set HF_HOME=C:\AI_Model_Cache
set PYTHONPATH=%~dp0;%PYTHONPATH%

REM P4000-specific environment variables
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
set CUDA_LAUNCH_BLOCKING=0

REM Check for ngrok token
if "%NGROK_AUTH_TOKEN%"=="" (
    echo ⚠️ NGROK_AUTH_TOKEN not set
    echo Get token from: https://ngrok.com
    echo Set with: set NGROK_AUTH_TOKEN=your_token
    echo Continuing with local access only...
)

REM Create outputs directory
if not exist "outputs" mkdir outputs

REM Show P4000 recommendations
echo 📊 P4000 Configuration:
echo - Max Resolution: 384x384
echo - Recommended Frames: 8
echo - Estimated Generation: 4-6 minutes
echo - VRAM Usage: 6-7GB
echo.

REM Start the P4000-optimized server
echo 🎬 Starting AI server on port 8122...
python p4000_server.py

pause</content>
<parameter name="filePath">remote_ai_setup/p4000_startup.bat