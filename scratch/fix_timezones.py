import re

files_to_fix = [
    "src/api/utils/models.py",
    "src/api/utils/user_models.py",
    "src/api/utils/credit_models.py"
]

for file_path in files_to_fix:
    print(f"Processing {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace datetime.now(timezone.utc) with datetime.now(timezone.utc).replace(tzinfo=None)
    # inside column defaults/onupdates to ensure naive timestamps are sent to asyncpg.
    new_content = content.replace(
        "datetime.now(timezone.utc)",
        "datetime.now(timezone.utc).replace(tzinfo=None)"
    )
    
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  Fixed timezone calls in {file_path}")
    else:
        print(f"  No changes needed in {file_path}")
