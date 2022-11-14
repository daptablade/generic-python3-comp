import subprocess
from pathlib import Path

LOCAL_EXECUTES = {"CGX": "cgx", "CCX": "ccx"}


def execute_cgx(infile: Path, run_folder: Path):
    """Run CGX with the batch input file to generate the mesh output files."""
    if LOCAL_EXECUTES["CGX"]:
        subprocess.run(
            LOCAL_EXECUTES["CGX"] + " -bg " + infile,
            cwd=run_folder,
            shell=True,
            check=True,
            capture_output=True,
        )
    else:
        raise ValueError("Need to specify an execution path for Calculix GraphiX.")


def execute_fea(infile: Path, run_folder: Path):
    """Run CCX to generate the FEA output files."""

    if LOCAL_EXECUTES["CCX"]:
        subprocess.run(
            LOCAL_EXECUTES["CCX"] + " " + infile.stem,
            cwd=run_folder,
            shell=True,
            check=True,
            capture_output=True,
        )
    else:
        raise ValueError("Need to specify an execution path for Calculix CrunchiX.")
