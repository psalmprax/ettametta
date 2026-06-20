import os

tests_dir = "/home/psalmprax/ALL_PROJECTS/ettametta/src/tests/e2e/tests"

fixed_count = 0

for root, dirs, files in os.walk(tests_dir):
    for file in files:
        if not (file.endswith('.ts') or file.endswith('.tsx')):
            continue
        abs_path = os.path.join(root, file)
        rel_to_tests = os.path.relpath(abs_path, tests_dir)
        
        # Check if the file is nested under a subdirectory of tests/
        is_nested = len(rel_to_tests.split(os.sep)) > 1
        
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        if is_nested:
            # Nested file: parent is tests/<category>/, path to helpers/ should be ../../helpers/auth
            if '../../../../helpers/auth' in content:
                content = content.replace('../../../../helpers/auth', '../../helpers/auth')
                modified = True
        else:
            # Flat file: parent is tests/, path to helpers/ should be ../helpers/auth
            if '../../../helpers/auth' in content:
                content = content.replace('../../../helpers/auth', '../helpers/auth')
                modified = True
                
        if modified:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count += 1
            print(f"Fixed imports in {rel_to_tests}")

print(f"Successfully fixed {fixed_count} files.")
