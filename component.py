#    Copyright 2023 Dapta LTD

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import sys
import os
import shutil
import subprocess
import importlib
from pathlib import Path
import requests
import traceback
from dotenv import load_dotenv

# load component specific environment variables
if Path(".env").is_file():
    load_dotenv()
EDITABLES_PATH = str(Path(__file__).parents[0] / "editables")
USER_FILES_PATH = os.getenv("USER_FILES_PATH", EDITABLES_PATH)
BE_API_HOST = os.getenv("BE_API_HOST", None)
MYPYPI_HOST = os.getenv("MYPYPI_HOST", None)
COMP_NAME = os.getenv("COMP_NAME", "component")
PYTHON_LIB = os.getenv(
    "PYTHON_LIB", "/home/non-root/.local/lib/python3.8/site-packages"
)
HOSTNAME = os.getenv("HOSTNAME")

sys.path.append(EDITABLES_PATH)
sys.path.append(PYTHON_LIB)

SETUP_IS_REQUIRED = True  # this is not re-initialised between runs
LOADED_MODULES = {}


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    params: dict = None,
    options: dict = None,
):

    if HOSTNAME in params["setup_hosts"]:
        print("already setup - return ...")
        return ("", {"params": params})

    print(f"starting setup on {HOSTNAME}")
    params["setup_hosts"].append(HOSTNAME)
    params["load_python_modules"] = ["setup.py", "compute.py"]
    basic_setup(params)

    # load input files
    load_modules = [f[:-3] for f in reversed(params.pop("load_python_modules"))]
    for m in load_modules:
        importlib.invalidate_caches()
        LOADED_MODULES[m] = importlib.import_module(m)
        importlib.reload(LOADED_MODULES[m])  # get user updates

    # execute setup
    try:
        resp = LOADED_MODULES["setup"].setup(inputs, outputs, parameters=params)
    except Exception:
        t = str(traceback.format_exc())
        # save setup output files to the user_storage in case of error
        if BE_API_HOST and params["outputs_folder_path"]:
            resp = post_ouput_files(
                ufpath=USER_FILES_PATH,
                be_api=BE_API_HOST,
                comp=COMP_NAME,
                outpath=str(params["outputs_folder_path"]),
                run_name=params["run_name"],
            )
            if "warning" in resp and resp["warning"]:
                t += "\n" + resp["warning"]
            if oom_check():
                t += "\nError 137 - System out of memory."
        raise ValueError(t)

    # response dictionary
    rdict = {}

    # basic checks
    if not isinstance(resp, dict):
        raise ValueError("User setup returned invalid response.")
    if inputs and "inputs" in resp:
        in_out_check(name="inputs", ref=inputs, new=resp["inputs"])
        rdict["inputs"] = resp.pop("inputs", None)
    if outputs and "outputs" in resp:
        in_out_check(name="outputs", ref=outputs, new=resp["outputs"])
        rdict["outputs"] = resp.pop("outputs", None)
    if "partials" in resp:
        if not isinstance(resp["partials"], dict):
            raise ValueError("partials should be a dictionary.")
        rdict["partials"] = resp.pop("partials", None)

    if "message" not in resp:
        msg = ""
    else:
        msg = resp.pop("message", None)

    if "parameters" in resp:
        if not isinstance(resp["parameters"], dict):
            raise ValueError("parameters should be a dictionary.")
        for key, val in resp["parameters"].items():
            if not key in params:  # avoid user overwriting setup data
                params[key] = val
            else:
                print(f"Warning - any updates to parameters data key {key} is ignored.")
        resp.pop("parameters", None)
    rdict["params"] = params

    # nothing should be left
    if resp:
        raise ValueError(f"illegal setup outputs {resp.keys()}")

    # save setup output files to the user_storage
    try:
        if BE_API_HOST and params["outputs_folder_path"]:
            resp = post_ouput_files(
                ufpath=USER_FILES_PATH,
                be_api=BE_API_HOST,
                comp=COMP_NAME,
                outpath=str(params["outputs_folder_path"]),
                run_name=params["run_name"],
            )
            if "warning" in resp and resp["warning"]:
                msg += resp["warning"]
    except Exception:
        t = str(traceback.format_exc())
        raise ValueError(t)

    return (msg, rdict)


def compute(
    params: dict = None,
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
):

    if SETUP_IS_REQUIRED:
        raise ValueError("Trying to run compute, but component has not been setup yet!")

    print("starting compute")

    if BE_API_HOST:
        # import connection input files from other components
        get_connection_files(
            "files.",
            inputs,
            infolder=params["inputs_folder_path"],
            run_name=params["run_name"],
        )

    # generic compute setup
    run_folder = Path(params["outputs_folder_path"])
    if not run_folder.is_dir():
        raise IsADirectoryError(f"{str(run_folder)} is not a folder.")
    inputs_folder = Path(params["inputs_folder_path"])
    user_input_files = params["user_input_files"]

    for file in user_input_files:
        if not (inputs_folder / file["filename"]).is_file():
            raise FileNotFoundError(
                f"{str(inputs_folder / file['filename'])} is not a file."
            )

    # execute compute
    try:
        resp = LOADED_MODULES["compute"].compute(
            inputs, outputs, partials, options, parameters=params
        )
    except Exception:
        t = str(traceback.format_exc())
        # save output files to the user_storage in case of error
        if BE_API_HOST and run_folder:
            resp = post_ouput_files(
                ufpath=USER_FILES_PATH,
                be_api=BE_API_HOST,
                comp=COMP_NAME,
                outpath=str(run_folder),
                run_name=params["run_name"],
            )
            if "warning" in resp and resp["warning"]:
                t += "\n" + resp["warning"]
            if oom_check():
                t += "\nError 137 - System out of memory."
        raise ValueError(t)

    # basic checks
    rdict = {}
    assert isinstance(resp, dict), "User compute returned invalid response."
    if "outputs" in resp:
        in_out_check(name="outputs", ref=outputs, new=resp["outputs"])
        rdict["outputs"] = resp.pop("outputs", None)
    if "partials" in resp:
        assert (
            isinstance(resp["partials"], dict)
            and partials.keys() == resp["partials"].keys()
        ), "partials not returned or keys mutated by compute."
        rdict["partials"] = resp.pop("partials", None)
    if "message" not in resp:
        msg = ""
    else:
        msg = resp.pop("message", None)

    # nothing should be left
    if resp:
        raise ValueError(f"illegal compute outputs {resp.keys()}")

    # save output files to the user_storage
    try:
        if BE_API_HOST and run_folder:
            resp = post_ouput_files(
                ufpath=USER_FILES_PATH,
                be_api=BE_API_HOST,
                comp=COMP_NAME,
                outpath=str(run_folder),
                run_name=params["run_name"],
            )
            if "warning" in resp and resp["warning"]:
                msg += resp["warning"]
    except Exception:
        t = str(traceback.format_exc())
        raise ValueError(t)

    return (msg, rdict)


### -------------------------------------------------- UTILS


def basic_setup(params):

    # setup empty outputs folders as required
    fpath = "editables"  # folder with user rwx permission
    params["inputs_folder_path"] = fpath
    input_files = ["setup.py", "compute.py", "requirements.txt"]
    dirs = []
    output_directory = "outputs"  # default
    p = fpath + "/" + output_directory
    dirs.append(p)
    params["outputs_folder_path"] = p

    if "user_input_files" in params:
        if not isinstance(params["user_input_files"], list):
            raise TypeError(
                "user_input_files should be list of dictionaries, each including a 'filename' key."
            )
        for i, file in enumerate(params["user_input_files"]):
            filename = safename(file["filename"])
            params["user_input_files"][i]["filename"] = filename
            input_files.append(filename)
            if filename[-3:] == ".py":
                params["load_python_modules"].append(filename)

    # create empty sub-directories for userfiles
    if dirs:
        make_dir(dirs)

    # import latest input files from pv
    if BE_API_HOST:
        get_input_files(
            ufpath=USER_FILES_PATH,
            be_api=BE_API_HOST,
            comp=COMP_NAME,
            input_files=input_files,
            inputs_folder_path=fpath,
            run_name=params["run_name"],
        )

    if MYPYPI_HOST:
        log_text = install("editables/requirements.txt", my_pypi=MYPYPI_HOST)
        print(log_text)
    else:
        log_text = local_install("editables/requirements.txt")
        print(log_text)

    global SETUP_IS_REQUIRED
    SETUP_IS_REQUIRED = False

    return None


def in_out_check(name, ref, new):
    if not isinstance(new, dict):
        raise TypeError(f"{name} has been mutated - should be a dictionary.")
    if not ref.keys() == new.keys():
        raise ValueError(f"{name} keys mutated.")
    for key in ref.keys():
        if not isinstance(new[key], dict):
            raise TypeError(
                f"{name}['{key}'] has been mutated - should be a dictionary."
            )
        if not ref[key].keys() == new[key].keys():
            raise ValueError(f"{name}['{key}'] keys mutated.")


def make_dir(dirs):
    for dir in dirs:
        dir_path = Path(dir)
        if dir_path.is_dir():
            shutil.rmtree(dir_path, ignore_errors=True)
        dir_path.mkdir()


def get_input_files(
    ufpath,
    be_api,
    comp,
    input_files,
    inputs_folder_path,
    subfolder="inputs",
    run_name="",
):

    headers = {"auth0token": ufpath.split("/")[-1]}

    for file in input_files:

        # check if input file exists
        params = {
            "file_name": file,
            "component_name": comp,
            "subfolder": subfolder,
            "run_name": run_name,
        }
        res = requests.get(
            f"http://{be_api}/be-api/v1/checkfilesexist",
            headers=headers,
            params=params,
        )
        res.raise_for_status()
        rdict = res.json()

        if rdict["response"]:
            # if file exists, then download it from server
            params = {
                "file": file,
                "component_name": comp,
                "subfolder": subfolder,
                "run_name": run_name,
            }
            res = requests.get(
                f"http://{be_api}/be-api/v1/getfiles",
                headers=headers,
                params=params,
            )
            res.raise_for_status()  # ensure we notice bad responses

            fpath = Path(inputs_folder_path, file)
            with open(fpath, "wb") as fd:
                for chunk in res.iter_content(chunk_size=128):
                    fd.write(chunk)
            print(f"Saved file: {str(fpath)}")

    print("Completed loading input files.")


def install(requirements_path, my_pypi):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--trusted-host",
            my_pypi,
            "-i",
            f"http://{my_pypi}/simple",
            "-r",
            requirements_path,
        ],
        stdout=subprocess.PIPE,
    )
    return result.stdout.decode()


def local_install(requirements_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            requirements_path,
        ],
        stdout=subprocess.PIPE,
    )
    return result.stdout.decode()


def safename(file):

    k = "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-"
    return "".join(list(filter(lambda x: x in k, str(file))))


def post_ouput_files(ufpath, be_api, comp, outpath, run_name):
    headers = {"auth0token": ufpath.split("/")[-1]}

    # list all files in outpath
    p = Path(outpath).glob("**/*")
    filepaths = [x for x in p if x.is_file()]

    # post to file server one by one
    warning = ""
    for filepath in filepaths:
        print(f"Uploading file: {filepath.name}")
        params = {
            "file_name": filepath.name,
            "component_name": comp,
            "subfolder": "outputs",
            "run_name": run_name,
        }
        with open(filepath, "rb") as f:
            try:
                res = requests.post(
                    f"http://{be_api}/be-api/v1/uploadfile",
                    headers=headers,
                    files={"file": ("", f, "application/octet-stream", {})},
                    data=params,
                )
                res.raise_for_status()  # ensure we notice bad responses
                res = res.json()
            except Exception as e:
                raise requests.exceptions.HTTPError(res.text)

        # catch failed file checks on server (e.g. for .py and requirements.txt files)
        if "filesaved" in res and res["filesaved"] == False:
            raise ValueError(
                f"Could not save file {str(filepath)}. Failed checks: {str(res['failed_checks'])}"
            )
        if "warning" in res:
            print(res)
            warning = res["warning"]

    return {"warning": warning}


def get_connection_files(prefix, inputs, infolder, run_name):

    for subtype in ["implicit", "setup"]:
        data = inputs[subtype]
        ks = [k for k in data.keys() if k.startswith(prefix)]
        if ks:
            filenames_raw = [data[key] for key in ks]
            filenames = [safename(file) for file in filenames_raw]
            if not filenames == filenames_raw:
                raise ValueError(
                    "input_files includes invalid filenames - valid characters are A-Z a-z 0-9 ._- only."
                )
            if subtype == "setup":
                # only get files if not already in input folder
                filenames = [
                    file for file in filenames if not Path(infolder, file).is_file()
                ]

            # import latest input files from pv
            if BE_API_HOST and filenames:
                get_input_files(
                    ufpath=USER_FILES_PATH,
                    be_api=BE_API_HOST,
                    comp=COMP_NAME,
                    input_files=filenames,
                    inputs_folder_path=infolder,
                    subfolder="connections",
                    run_name=run_name,
                )


def oom_check():

    with open(
        "/sys/fs/cgroup/memory/memory.max_usage_in_bytes", "r", encoding="utf-8"
    ) as f:
        mem_max = int(f.readline())

    with open(
        "/sys/fs/cgroup/memory/memory.limit_in_bytes", "r", encoding="utf-8"
    ) as f:
        mem_limit = int(f.readline())

    min_margin = 10 * 1024**2  # 10Mb in bytes
    if (mem_limit - mem_max) <= min_margin:
        return True
    else:
        return False


if __name__ == "__main__":
    inputs = {"design": {}, "implicit": {}, "setup": {}}
    outputs = {"design": {}, "implicit": {}, "setup": {}}
    params = {"setup_hosts": [], "user_input_files": [{"filename": "temp.py"}]}
    (msg, rdict) = setup(
        inputs=inputs, outputs=outputs, partials={}, params=params, options={}
    )
    compute(
        inputs=inputs, outputs=outputs, partials={}, params=rdict["params"], options={}
    )
