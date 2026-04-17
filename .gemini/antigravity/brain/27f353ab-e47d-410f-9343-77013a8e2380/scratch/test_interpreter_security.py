import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from services.interpreter.sandbox_runner import validate_code

test_cases = [
    ("print('Hello World')", True),
    ("import os; os.system('ls')", False),
    ("__import__('os').system('ls')", False),
    ("eval('import os')", False),
    ("open('/etc/passwd')", False),
    ("import subprocess; subprocess.run(['ls'])", False),
    ("class A: pass\nA().__class__.__base__", False), # Dunder access
]

def run_tests():
    print("Running Interpreter Security Tests...")
    all_passed = True
    for code, expected in test_cases:
        is_safe, reason = validate_code(code)
        if is_safe == expected:
            print(f"✅ PASS: {code[:30]}... -> {'Safe' if is_safe else 'Blocked'}")
        else:
            print(f"❌ FAIL: {code[:30]}... -> Expected {expected}, got {is_safe} ({reason})")
            all_passed = False
    
    if all_passed:
        print("\n🏆 ALL SECURITY TESTS PASSED")
    else:
        print("\n⚠️ SOME TESTS FAILED")

if __name__ == "__main__":
    run_tests()
