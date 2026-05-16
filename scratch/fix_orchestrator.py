import sys
import os
import re

path = "/app/src/services/nexus_engine/orchestrator.py"
if not os.path.exists(path):
    path = "/home/psalmprax/ALL_PROJECTS/ettametta/src/services/nexus_engine/orchestrator.py"

with open(path, "r") as f:
    code = f.read()

# The pattern to replace is the one we tried to inject
pattern = r"import subprocess\nimport os\n.*?audio_uri = voiceover_paths\[0\] if voiceover_paths else music_path"

correct_logic = """import subprocess
import os

            # Concatenate all voiceovers into a single master file
            master_voiceover = f"temp/voice/master_{job_id}.mp3"
            if len(voiceover_paths) > 1:
                self.logger.info(f"[Nexus] Stitching {len(voiceover_paths)} voiceovers...")
                os.makedirs("temp/voice", exist_ok=True)
                with open(f"temp/voice/list_{job_id}.txt", "w") as f:
                    for vp in voiceover_paths:
                        f.write(f"file '{os.path.abspath(vp)}'\\n")
                subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"temp/voice/list_{job_id}.txt", "-c", "copy", master_voiceover])
                audio_uri = master_voiceover
            else:
                audio_uri = voiceover_paths[0] if voiceover_paths else music_path

            # Calculate total duration for Remotion
            try:
                probe_target = audio_uri if audio_uri and os.path.exists(audio_uri) else None
                if probe_target:
                    res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", probe_target], capture_output=True, text=True)
                    total_duration_sec = float(res.stdout.strip())
                    total_frames = int(total_duration_sec * 30) + 30
                    props["duration_in_frames"] = total_frames
                    self.logger.info(f"[Nexus] Master duration detected: {total_duration_sec}s ({total_frames} frames)")
            except Exception as e:
                self.logger.error(f"[Nexus] Duration probe failed: {e}")"""

# Let's try a safer replacement by finding the broken block
# I'll look for the unique strings I injected
if "import subprocess" in code and "total_duration_sec" in code:
    # It's broken. Let's find the start of the injection and the end of the original line
    start_marker = "import subprocess\nimport os\n"
    end_marker = "audio_uri = voiceover_paths[0] if voiceover_paths else music_path"
    
    start_idx = code.find(start_marker)
    end_idx = code.find(end_marker) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        new_code = code[:start_idx] + correct_logic + code[end_idx:]
        with open(path, "w") as f:
            f.write(new_code)
        print("Successfully fixed orchestrator.py")
    else:
        print(f"Could not find markers: {start_idx}, {end_idx}")
else:
    print("Code doesn't seem to contain the broken injection.")
