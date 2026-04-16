@echo off
REM NVIDIA P4000 Multi-Model AI Server Startup Script

echo 🚀 Starting ettametta P4000 Multi-Model AI Server...
echo 🎨 Supports: AnimateDiff, LTX-Video, ZeroScope, Lite4K
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

REM P4000 multi-model environment variables
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

REM Show model information
echo 📋 Available Models:
echo    • animatediff: Character animations (384p, 8 frames, 4-6min)
echo    • ltx_video: High-quality video (320p, 6 frames, 6-8min)
echo    • zeroscope: Creative content (320p, 6 frames, 5-7min)
echo    • lite4k: Fast generation (256p, 4 frames, 3-5min)
echo.

REM Show P4000 recommendations
echo 🎯 P4000 Multi-Model Recommendations:
echo - Use AnimateDiff for most animations (most reliable)
echo - Try LTX-Video for higher quality scenes
echo - Use Lite4K for quick testing
echo - Monitor VRAM usage: nvidia-smi
echo.

REM Start the multi-model server
echo 🎬 Starting multi-model AI server on port 8122...
python p4000_server_multi.py

pause</content>
<parameter name="filePath">remote_ai_setup/start_multi_server.bat