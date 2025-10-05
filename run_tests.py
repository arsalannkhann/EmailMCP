"""
Comprehensive test runner for EmailMCP
Runs all tests and generates coverage report
"""
import sys
import os
import subprocess

def main():
    """Run all tests with coverage"""
    print("=" * 70)
    print("EmailMCP Comprehensive Test Suite")
    print("=" * 70)
    print()
    
    # Change to repository root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_root)
    
    # Run pytest with coverage
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--cov=src/mcp",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--tb=short",
        "-x"  # Stop on first failure for debugging
    ]
    
    print("Running tests...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ All tests passed!")
        print()
        print("Coverage report generated in htmlcov/index.html")
    else:
        print("❌ Some tests failed!")
        print("Review the output above for details.")
    print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
