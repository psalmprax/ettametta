import importlib.util

def check_module_available(module_name: str) -> bool:
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except Exception:
        return False

print(f"realesrgan: {check_module_available('realesrgan')}")
print(f"basicsr: {check_module_available('basicsr')}")
print(f"cv2: {check_module_available('cv2')}")
