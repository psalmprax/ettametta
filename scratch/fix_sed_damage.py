import os
import re

def fix_sed_damage(path):
    with open(path, 'r') as f:
        content = f.read()
    
    # 1. Fix the "Optional -> Any" mistake
    # If it was Optional[dict[str, Any]] and I changed it to Any[dict[str, Any]], fix it.
    # Actually, if I just changed Optional to Any, now I might have Any[Something].
    content = re.sub(r'Any\[(.+)\]', r'\1 | None', content)
    
    # 2. Fix trailing '| None | None'
    content = content.replace('| None | None', '| None')
    
    # 3. Fix 'any | None' to 'Any | None' (builtin vs typing)
    content = content.replace('any | None', 'Any | None')
    
    # 4. Modernize Union[A, B] -> A | B
    def replace_union(match):
        inner = match.group(1)
        parts = [p.strip() for p in inner.split(',')]
        return " | ".join(parts)
    
    content = re.sub(r'Union\[([^\[\]]+)\]', replace_union, content)

    # 5. Fix common Dict/List stragglers
    content = content.replace('Dict[', 'dict[')
    content = content.replace('List[', 'list[')
    content = content.replace('Tuple[', 'tuple[')

    with open(path, 'w') as f:
        f.write(content)
    return True

def main():
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                fix_sed_damage(path)
    print("Sed damage control complete.")

if __name__ == "__main__":
    main()
