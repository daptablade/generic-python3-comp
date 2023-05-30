import os
import subprocess
from pathlib import Path


def run_ccx_preCICE(infile: Path, run_folder: Path, participant=None, env=None):
    """Run preCICE Calculix adaptor."""

    if not infile.is_file():
        raise ValueError(f"infile is not valid file path: {infile}")

    if not run_folder.is_dir():
        raise ValueError(f"run_folder is not valid folder path: {run_folder}")

    if not isinstance(participant, str):
        raise ValueError(
            f"participant is not a valid participant name string: {participant}"
        )

    if env is isinstance(env, dict):
        for k, v in env:
            print(f"Setting environment variable {k} to value {v}")
            os.environ[k] = str(v)

    resp = subprocess.run(
        "ccx_preCICE"
        + " -i "
        + str(infile.stem)
        + " -precice-participant "
        + str(participant),
        cwd=run_folder,
        shell=True,
        check=False,
        capture_output=True,
        env=os.environ,
    )
    return {"stdout": resp.stdout.decode("ascii"), "returncode": resp.returncode}
