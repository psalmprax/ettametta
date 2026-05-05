import os
import re

directory = "/home/psalmprax/ALL_PROJECTS/ettametta/src/services/discovery/"
scanners = [f for f in os.listdir(directory) if f.endswith("_scanner.py")]

for scanner in scanners:
    file_path = os.path.join(directory, scanner)
    with open(file_path, "r") as f:
        content = f.read()
    
    # Update scan_trends signature to accept **kwargs
    # Matches: def scan_trends(self, niche: str, ...):
    # or: async def scan_trends(self, niche: str, ...):
    
    pattern = r"(async\s+)?def\s+scan_trends\s*\(([^)]*)\)"
    
    def replacement(match):
        async_prefix = match.group(1) or ""
        args = match.group(2)
        if "**kwargs" in args:
            return match.group(0)
        
        # Add **kwargs to the end of the argument list
        if args.strip().endswith(","):
            new_args = args.strip() + " **kwargs"
        else:
            new_args = args.strip() + ", **kwargs"
        
        return f"{async_prefix}def scan_trends({new_args})"

    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(file_path, "w") as f:
            f.write(new_content)
        print(f"Updated {scanner}")
