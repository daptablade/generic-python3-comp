#    Copyright 2022 Dapta LTD

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
import subprocess
import importlib
from pathlib import Path
import requests

NAME = "generic-python3-comp|driver"
USER_FILES_PATH = os.getenv("USER_FILES_PATH")
BE_API_HOST = os.getenv("BE_API_HOST")
MYPYPI_HOST = os.getenv("MYPYPI_HOST")
COMP_NAME = os.getenv("COMP_NAME")

sys.path.append(str(Path(__file__).parents[0] / "editables"))


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    params: dict = None,
    **kwargs,
):

    print("starting setup")

    # import latest input files from pv
    if BE_API_HOST:
        get_input_files(ufpath=USER_FILES_PATH, be_api=BE_API_HOST, comp=COMP_NAME)

    if MYPYPI_HOST:
        log_text = install("editables/requirements.txt", my_pypi=MYPYPI_HOST)
        print(log_text)

    # load input files
    importlib.invalidate_caches()
    user_setup = importlib.import_module("setup")
    importlib.reload(user_setup)  # get user updates

    # execute setup
    resp = user_setup.setup(inputs, outputs, partials, params)

    # basic checks
    rdict = {}
    assert isinstance(resp, dict), "User setup returned invalid response."
    if inputs:
        assert (
            "inputs" in resp
            and isinstance(resp["inputs"], dict)
            and inputs.keys() == resp["inputs"].keys()
        ), "inputs not returned or keys mutated by setup."
        rdict["inputs"] = resp.pop("inputs", None)
    if outputs:
        assert (
            "outputs" in resp
            and isinstance(resp["outputs"], dict)
            and outputs.keys() == resp["outputs"].keys()
        ), "outputs not returned or keys mutated by setup."
        rdict["outputs"] = resp.pop("outputs", None)
    if "partials" in resp:
        assert isinstance(resp["partials"], dict), "partials should be a dictionary."
        rdict["partials"] = resp.pop("partials", None)

    if "message" not in resp:
        msg = ""
    else:
        msg = resp.pop("message", None)

    if resp:  # remaining keys get saved to setup_data accessible in compute
        rdict.update(resp)

    return (msg, rdict)


def compute(
    setup_data: dict = None,
    params: dict = None,
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
    root_folder: str = None,
    **kwargs,
):
    print("starting compute")

    # load input files
    importlib.invalidate_caches()
    user_compute = importlib.import_module("compute")
    importlib.reload(user_compute)  # get user updates

    # execute compute
    resp = user_compute.compute(
        setup_data, params, inputs, outputs, partials, options, root_folder
    )

    # basic checks
    rdict = {}
    assert isinstance(resp, dict), "User compute returned invalid response."
    if outputs and "outputs" in resp:
        assert (
            isinstance(resp["outputs"], dict)
            and outputs.keys() == resp["outputs"].keys()
        ), "outputs not returned or keys mutated by compute."
        rdict["outputs"] = resp["outputs"]
    elif "outputs" in resp:
        rdict["outputs"] = resp["outputs"]
    if partials and "partials" in resp:
        assert (
            isinstance(resp["partials"], dict)
            and partials.keys() == resp["partials"].keys()
        ), "partials not returned or keys mutated by compute."
        rdict["partials"] = resp["partials"]
    elif "partials" in resp:
        rdict["partials"] = resp["partials"]

    # check if there are parameter updates
    if any([key not in ["outputs", "partials", "message"] for key in resp]):
        # update setup_data dictionary for param connections
        for key in resp:
            if key not in ["outputs", "partials", "message"]:
                assert key in setup_data, f"illegal compute output {key}"
                rdict[key] = resp[key]

    if "message" not in resp:
        msg = ""
    else:
        msg = resp["message"]

    return (msg, rdict)


### -------------------------------------------------- UTILS


def get_input_files(ufpath, be_api, comp):

    headers = {"auth0token": ufpath.split("/")[-2]}
    files = ["setup.py", "compute.py", "requirements.txt"]

    for file in files:

        # check if input file exists
        params = {"file_name": file, "component_name": comp}
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
                "file": comp + "/inputs/" + file,
                "content_type": "text/plain",
            }
            res = requests.get(
                f"http://{be_api}/be-api/v1/getfiles",
                headers=headers,
                params=params,
            )
            res.raise_for_status()  # ensure we notice bad responses
            with open(Path("editables") / file, "w") as f:
                f.write(res.text)

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
