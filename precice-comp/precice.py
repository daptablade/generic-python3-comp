import os
import signal
import subprocess
from pathlib import Path
import threading
from time import sleep


def run_ccx_preCICE(
    infile: Path,
    run_folder: Path,
    participant=None,
    env=None,
    precice_config=None,
    tools=Path("/app/precice-calculix-comp/tools"),
):
    """Run preCICE Calculix adaptor."""

    if not infile.is_file():
        raise ValueError(f"infile is not valid file path: {infile}")

    if not run_folder.is_dir():
        raise ValueError(f"run_folder is not valid folder path: {run_folder}")

    FLAG_connection_file_monitoring = get_config_file(precice_config, participant)
    if FLAG_connection_file_monitoring:
        event = threading.Event()
        t1 = threading.Thread(
            daemon=True,
            target=run_background_script,
            kwargs={
                "run_folder": run_folder,
                "script": "copy_connection_file.bash",
                "stop_on": event,
                "tools_path": tools,
                "args": [
                    participant,
                    '{"Calculix1":"beam-1", "Calculix2":"beam-2"}',
                ],  # TODO
            },
        )
        t2 = threading.Thread(
            daemon=True,
            target=run_background_script,
            kwargs={
                "run_folder": run_folder,
                "script": "connection_file_delete.bash",
                "stop_on": event,
                "tools_path": tools,
                "args": None,
            },
        )
        t3 = threading.Thread(
            daemon=True,
            target=run_background_script,
            kwargs={
                "run_folder": run_folder,
                "script": "monitor_connections.bash",
                "stop_on": event,
                "tools_path": tools,
                "args": None,
            },
        )
        t3.start()

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

    if FLAG_connection_file_monitoring:
        event.set()  # stop deamon threads
        t1.join()
        t2.join()

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


def get_config_file(infile: Path, participant=None):
    # default
    FLAG_connection_file_monitoring = False

    if not infile.is_file():
        raise ValueError(f"infile is not valid file path: {infile}")

    # read component precice config file
    with open(infile, "r") as f:
        data = f.readlines()

    # determine if the component in a requester/accessor component (from/to in m2n)
    m2n, l_index = [
        (l.strip(), ii)
        for ii, l in enumerate(data)
        if l.strip().startswith("<m2n:sockets")
    ][0]
    m2n_dict = {
        pair.split("=")[0]: (
            pair.split("=")[1].replace('"', "")
            if pair.split("=")[1].startswith('"')
            else pair.split("=")[1].replace("'", "")
        )
        for pair in m2n.split(" ")
        if "=" in pair
    }

    if m2n_dict["from"] == participant:
        # 1) update the shared folder path from "../../pvc_shared" to "../../pvc_shared_copy"
        data[l_index] = data[l_index].replace("pvc_shared", "pvc_shared_copy")
        with open(infile, "w") as f:
            f.writelines(data)

        # 2) set run connection file monitoring falg to TRUE
        FLAG_connection_file_monitoring = True

    return FLAG_connection_file_monitoring


def run_background_script(run_folder, script, stop_on, tools_path, args):
    if not args:
        cmd = f"/bin/bash {tools_path / script}"
    else:
        cmd = f"/bin/bash {tools_path / script}"
        for arg in args:
            cmd += f" {arg}"
    with open(run_folder / f"{script}.log", "w") as log:
        with subprocess.Popen(
            cmd, cwd=tools_path, shell=True, env=os.environ, preexec_fn=os.setsid, stdout= 
        ) as proc:
            log.write("Script execution started.\n")
            log.write(proc.stdout.read().decode("utf-8"))

    while not stop_on.is_set():
        with open(run_folder / f"{script}.log", "w") as log:
            log.write("compute still running ....\n")
        sleep(1)

    os.killpg(
        os.getpgid(proc.pid), signal.SIGTERM
    )  # Send the signal to all the process groups


if __name__ == "__main__":
    run_folder = Path("/home/olivia/tutorials/perpendicular-flap/fluid-openfoam")
    run_openfoam_blockMesh(run_folder)
    run_openfoam_preCICE(run_folder, tools=Path("/home/olivia/tutorials/tools"))
