import os
import requests
import zipfile
import json
from pathlib import Path

RESCALE_HOST = os.getenv("RESCALE_HOST")
USER_FILES_PATH = os.getenv("USER_FILES_PATH")

JOB_TEMPLATE = {
    "name": "test",
    "command": "python paraboloid.py",
    "analysis": {"code": "miniconda", "version": "4.8.4"},  # from analyses.json
    "hardware": {
        "coreType": "emerald",
        "coresPerSlot": 1,
        "slots": 1,
        "walltime": 1,
    },  # from coretypes.json
    "archiveFilters": [{"selector": "*"}],  # all outputs are recovered
    "API_token_name": "rescale",  # NOT TOKEN VALUE, but key from user_app_metadata
}


def main(job, inputs_paths, run_folder: Path):
    # check basic input job keys and values
    headers = {"auth0token": USER_FILES_PATH.split("/")[-1]}
    params = {
        "job": json.dumps(job),
    }
    try:
        res = requests.post(
            f"http://{RESCALE_HOST}/checkjob", headers=headers, data=params
        )
        res.raise_for_status()  # ensure we notice bad responses
    except Exception as e:
        raise requests.exceptions.HTTPError(res.text)

    # zip inputs
    input_zip = run_folder / "input_files.zip"
    with zipfile.ZipFile(input_zip, mode="w") as archive:
        for file in inputs_paths:
            if not file.is_file():
                raise FileNotFoundError(f"Cannot find input file {file}")
            archive.write(file, arcname=file.name)

    # call rescale service to run job
    try:
        res = requests.post(
            f"http://{RESCALE_HOST}/main",
            headers=headers,
            data=params,
            files={"file": open(input_zip, "rb")},
            stream=True,
        )
        res.raise_for_status()
    except Exception as e:
        raise requests.exceptions.HTTPError(res.text)

    fpath = run_folder / "output_files_downloaded.zip"
    with open(fpath, "wb") as fd:
        for chunk in res.iter_content(chunk_size=128):
            fd.write(chunk)
    print(f"Saved file: {str(fpath)}")

    # unzip outputs
    with zipfile.ZipFile(fpath, mode="r") as f:
        f.extractall(run_folder)

    # delete archive
    os.remove(fpath)
