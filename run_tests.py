import pytest
import sys

if __name__ == "__main__":
    # Run pytest with minimal output
    sys.exit(pytest.main(["-v", "--color=no", "-p", "no:warnings", "tests/test_auth.py"]))
