import os
import re

def fix_python_file(path):
    with open(path, 'r') as f:
        content = f.read()
    
    # Check if Any is used as a type hint pattern
    any_used = re.search(r'[:\[]\s*Any\b', content) or re.search(r'->\s*Any\b', content)
    
    # Check typing imports
    typing_line_match = re.search(r'from typing import (.+)', content)
    
    if typing_line_match:
        imports_text = typing_line_match.group(1)
        imports = [i.strip() for i in imports_text.split(',')]
        
        # Remove modernized types (including accidental lower-case ones from aggressive sed)
        new_imports = [i for i in imports if i not in ['List', 'Dict', 'Tuple', 'Optional', 'dict', 'list', 'tuple', 'optional']]
        
        # Add Any if needed and not present
        if any_used and 'Any' not in new_imports:
            new_imports.append('Any')
            
        if not new_imports:
            # Entire typing import is now unused
            new_content = content.replace(typing_line_match.group(0) + '\n', '')
            if new_content == content: # Try without newline
                new_content = content.replace(typing_line_match.group(0), '')
        else:
            new_imports_text = "from typing import " + ", ".join(sorted(list(set(new_imports))))
            new_content = content.replace(typing_line_match.group(0), new_imports_text)
            
        if new_content != content:
            with open(path, 'w') as f:
                f.write(new_content)
            return True
    elif any_used:
        # Any used but no typing import at all? Add it.
        # This is rare but possible.
        new_content = "from typing import Any\n" + content
        with open(path, 'w') as f:
            f.write(new_content)
        return True
        
    return False

def main():
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if fix_python_file(path):
                    print(f"Fixed {path}")

if __name__ == "__main__":
    main()
