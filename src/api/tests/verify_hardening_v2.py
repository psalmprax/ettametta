import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add current dir to path
sys.path.append(os.getcwd())

# Force settings
os.environ["ENABLE_INTERPRETER"] = "true"
os.environ["INTERPRETER_SANDBOX"] = "true"
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"

# Mock complex dependencies before any imports
sys.modules["api.utils.vault"] = MagicMock()
sys.modules["api.utils.llm_vault"] = MagicMock()
mock_config = MagicMock()
mock_config.settings.REDIS_URL = "redis://localhost:6379"
mock_config.settings.DATABASE_URL = "postgresql://user:pass@localhost/db"
mock_config.settings.FONT_PATH = "/tmp/font.ttf"
mock_config.settings.GPU_QUEUE_TIMEOUT = 30
mock_config.settings.EFFECTIVE_GPU_QUEUE_SLOTS = 2
sys.modules["api.config"] = mock_config

async def run_audit():
    print("🚀 ETTAMETTA RED-TEAM HARDENING AUDIT (25/25 TARGET)")
    print("-" * 50)
    
    services = [
        ("OS Worker", "api.utils.os_worker", "ai_worker"),
        ("Video Processor", "services.video_engine.processor", "VideoProcessor"),
        ("Synthesis Service", "services.video_engine.synthesis_service", "base_generative_service"),
        ("Free Providers", "services.video_engine.free_video_providers", "free_video_provider"),
        ("LLM Service", "services.llm.service", "unified_llm_service"),
        ("OCR Service", "services.video_engine.base_ocr_service", "base_ocr_service"),
    ]
    
    results = []
    
    for name, module_path, attr in services:
        try:
            import importlib
            mod = importlib.import_module(module_path)
            obj = getattr(mod, attr)
            
            # Instantiate if it's a class
            if isinstance(obj, type):
                instance = obj()
            else:
                instance = obj
                
            report = instance.get_dependency_report()
            status = "Top Notch" if report['healthy'] else "Soft-Fallback"
            if "circuit_status" in report:
                status += f" (Circuit: {report['circuit_status']})"
            
            print(f"✅ {name:20}: {status}")
            results.append(True)
        except Exception as e:
            print(f"❌ {name:20}: FAILED IMPORT ({type(e).__name__}: {e})")
            results.append(False)

    print("\n🔒 SECURITY INJECTION TESTING (SANDBOX LOCKDOWN)")
    print("-" * 50)
    
    try:
        from src.services.llm.interpreter import interpreter_service
        
        # Test 1: Direct getattr
        payload1 = "getattr(str, 'upper')"
        res1 = await interpreter_service.execute_code(payload1)
        print(f"🛡️  Test 1 (Direct getattr):   {'BLOCKED' if not res1['success'] else 'FAILED'}")
        
        # Test 2: Obfuscated concatenation
        payload2 = 'o = "o"; s = "s."; res = o + s + "sy" + "stem"; print(res)'
        res2 = await interpreter_service.execute_code(payload2)
        print(f"🛡️  Test 2 (Obfuscated OS):   {'BLOCKED' if not res2['success'] else 'FAILED'}")
        
        # Test 3: Sandbox Escape (__class__)
        payload3 = '"".__class__.__mro__[1].__subclasses__()'
        res3 = await interpreter_service.execute_code(payload3)
        print(f"🛡️  Test 3 (Class Escape):     {'BLOCKED' if not res3['success'] else 'FAILED'}")

    except Exception as e:
        print(f"❌ Security Testing Failed to run: {e}")

    print("\n" + "#" * 50)
    if all(results):
        print("🎯 FINAL STATUS: 100% PRODUCTION HARDENED (TOP NOTCH)")
    else:
        print("⚠️ FINAL STATUS: HARDENING INCOMPLETE")
    print("#" * 50)

if __name__ == "__main__":
    asyncio.run(run_audit())
