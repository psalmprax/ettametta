@echo off
REM NVIDIA P4000 8GB - AI Video Generation Test

echo 🚀 Testing P4000 8GB AI Video Generation Setup
echo.

REM Check if in virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo ❌ Not in virtual environment!
    echo Run: p4000_env\Scripts\activate
    pause
    exit /b 1
)

echo 📊 Checking hardware...
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('CUDA Version:', torch.version.cuda if torch.cuda.is_available() else 'N/A')"

echo.
echo 🔍 Checking P4000 GPU info...
python -c "import torch; print('GPU Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No CUDA GPU'); print('VRAM Total:', torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0, 'GB')"

echo.
echo 📦 Testing model loading...
python -c "from diffusers import AnimateDiffPipeline; print('✅ Diffusers installed')"

echo.
echo 🎯 Testing P4000 config...
python -c "from p4000_config import get_p4000_optimization_settings; config = get_p4000_optimization_settings(); print('✅ P4000 config loaded'); print('Max resolution:', config['animation']['max_resolution'])"

echo.
echo 🎬 Testing basic generation (fast test)...
python -c "
import torch
from animatediff_laptop_inference import generate_animatediff_laptop
import asyncio

async def test():
    try:
        # Quick test with minimal settings
        result = await generate_animatediff_laptop(
            'test animation of a cat', 
            num_frames=4,  # Very minimal for test
            height=256, 
            width=256
        )
        print('✅ Generation test successful!')
        print('Result:', result.get('video_url', 'No URL'))
    except Exception as e:
        print('❌ Generation test failed:', str(e))

asyncio.run(test())
"

echo.
echo 📈 Performance recommendations:
echo - Use 384x384 resolution for best quality
echo - Limit animations to 8-12 frames
echo - Expect 4-6 minutes per generation
echo - Monitor VRAM with: nvidia-smi

echo.
echo 🎉 P4000 test complete!
echo If all checks passed, your P4000 is ready for AI video generation!

pause</content>
<parameter name="filePath">remote_ai_setup/test_p4000.bat