import pytest
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

if __name__ == "__main__":
    f = io.StringIO()
    with redirect_stdout(f), redirect_stderr(f):
        ret = pytest.main(["-v", "--color=no", "-p", "no:warnings", "tests/"])
    
    with open("test_result_internal.txt", "w", encoding="utf-8") as out:
        out.write(f.getvalue())
    
    sys.exit(ret)
