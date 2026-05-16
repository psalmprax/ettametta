import sys

with open('/tmp/main.py', 'r') as f:
    content = f.read()

old_code = """def load_enhancers(upscale_factor=2):
    global face_enhancer, upscaler_model
    if face_enhancer is None:"""

new_code = """def load_enhancers(upscale_factor=2):
    global face_enhancer, upscaler_model
    if GFPGANer is None or RealESRGANer is None or RRDBNet is None:
        print("⚠️ Enhancement libraries not available, skipping load.")
        return None, None
    if face_enhancer is None:"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('/tmp/main.py', 'w') as f:
        f.write(content)
    print("Patch applied successfully")
else:
    print("Could not find code block to patch")
    sys.exit(1)
