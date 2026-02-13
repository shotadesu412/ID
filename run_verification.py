
import pytest
import sys
import os

if __name__ == "__main__":
    # Add current directory to sys.path
    sys.path.append(os.getcwd())
    
    # Run pytest on the new test files
    args = ["-v", "--color=yes", "tests/test_admin_feature.py", "tests/test_signup_feature.py"]
    print(f"Running pytest with args: {args}")
    sys.exit(pytest.main(args))
