import subprocess
import sys
from pathlib import Path


def test_generated_result_sections_are_current():
    root = Path(__file__).parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "make_results_tables.py"), "--check"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
