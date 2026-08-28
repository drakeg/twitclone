"""Regression coverage for application import boundaries."""

import subprocess
import sys


def test_application_imports_cleanly_in_fresh_python_process():
    result = subprocess.run(
        [sys.executable, "-c", "import application; assert application.application is not None"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
