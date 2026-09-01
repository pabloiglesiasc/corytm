import subprocess
import tempfile
from pathlib import Path

import pytest

_CORE_PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]


@pytest.mark.transport
def test_entry_point_runs_independent_of_caller_working_directory() -> None:
    with tempfile.TemporaryDirectory() as invocation_directory:
        result = subprocess.run(
            ["uv", "run", "--project", str(_CORE_PROJECT_DIRECTORY), "corytm"],
            cwd=invocation_directory,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "Rendered 88200 samples" in result.stdout

        rendered_files = list(Path(invocation_directory).glob("*.wav"))
        assert len(rendered_files) == 1
