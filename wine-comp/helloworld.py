import subprocess
from pathlib import Path


def execute_helloworld(run_folder: Path):
    """Run helloworld windows executable and save text output to file."""

    resp = subprocess.run(
        "wine /app/wine-comp/helloworld.exe > helloworld.out",
        cwd=run_folder,
        shell=True,
        check=False,
        capture_output=True,
    )
    return {"stdout": resp.stdout.decode("ascii"), "returncode": resp.returncode}
