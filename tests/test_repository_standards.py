import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repository_standards_validator_passes_current_repository():
    result = subprocess.run(
        [sys.executable, "scripts/check_repository_standards.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "repository standards and README badges are consistent" in result.stdout
