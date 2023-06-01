import os
import subprocess
from pathlib import Path


def run_ccx_preCICE(infile: Path, run_folder: Path, participant=None, env=None):
    """Run preCICE Calculix adaptor."""

    if not infile.is_file():
        raise ValueError(f"infile is not valid file path: {infile}")

    if not run_folder.is_dir():
        raise ValueError(f"run_folder is not valid folder path: {run_folder}")

    cmd = f"ccx_preCICE -i {infile.stem}"
    if isinstance(participant, str):
        cmd += f" -precice-participant {participant}"

    if env is isinstance(env, dict):
        for k, v in env:
            print(f"Setting environment variable {k} to value {v}")
            os.environ[k] = str(v)

    resp = subprocess.run(
        cmd,
        cwd=run_folder,
        shell=True,
        check=False,
        capture_output=True,
        env=os.environ,
    )
    return {"stdout": resp.stdout.decode("ascii"), "returncode": resp.returncode}


def run_openfoam_preCICE(
    run_folder: Path, env=None, tools=Path("/app/precice-openfoam-comp/tools")
):
    """Run openfoam adaptor."""

    if not run_folder.is_dir():
        raise ValueError(f"run_folder is not valid folder path: {run_folder}")

    cmd = "/bin/bash -c 'source /usr/lib/openfoam/openfoam2212/etc/bashrc && touch fluid-openfoam.foam "
    cmd += f"&& {str(tools /'run-openfoam.sh')} \"$@\" "
    cmd += f"&& source {str(tools /'openfoam-remove-empty-dirs.sh')} && openfoam_remove_empty_dirs' "

    if env is isinstance(env, dict):
        for k, v in env:
            print(f"Setting environment variable {k} to value {v}")
            os.environ[k] = str(v)

    resp = subprocess.run(
        cmd,
        cwd=run_folder,
        shell=True,
        check=False,
        capture_output=True,
        env=os.environ,
    )
    return {"stdout": resp.stdout.decode("ascii"), "returncode": resp.returncode}


def run_openfoam_blockMesh(run_folder: Path, case: str = ""):
    if not run_folder.is_dir():
        raise ValueError(f"run_folder is not valid folder path: {run_folder}")

    cmd = "/bin/bash -c 'source /usr/lib/openfoam/openfoam2212/etc/bashrc && blockMesh'"
    if case and isinstance(case, str):
        cmd += f" -case {case}"

    resp = subprocess.run(
        cmd,
        cwd=run_folder,
        shell=True,
        check=False,
        capture_output=True,
        env=os.environ,
    )
    return {"stdout": resp.stdout.decode("ascii"), "returncode": resp.returncode}


if __name__ == "__main__":
    run_folder = Path("/home/olivia/tutorials/perpendicular-flap/fluid-openfoam")
    run_openfoam_blockMesh(run_folder)
    run_openfoam_preCICE(run_folder, tools=Path("/home/olivia/tutorials/tools"))
