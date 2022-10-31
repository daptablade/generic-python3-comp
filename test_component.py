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

import os
import sys
import pytest
import subprocess

from urllib import response
import grpc
from google.protobuf.struct_pb2 import Struct
from google.protobuf import json_format

import component_api
from component_pb2 import ComponentRequest
from component_pb2_grpc import ComponentStub

from pathlib import Path
from dotenv import load_dotenv

from component import get_input_files, install

load_dotenv()  # read from local .env file
USER_FILES_PATH = os.getenv("USER_FILES_PATH")
BE_API_HOST = os.getenv("BE_API_HOST")
MYPYPI_HOST = os.getenv("MYPYPI_HOST")
COMP_NAME = os.getenv("COMP_NAME")

SETUP_IN = [
    {
        "params": {"x": 1.0},
        "inputs": {"x": "default"},
        "outputs": {"fx": "default"},
    }
]

SETUP_OUT = [
    {
        "inputs": {"x": 1.0},
        "outputs": {"fx": 0.0},
    }
]

COMPUTE_OUT = [
    {
        "outputs": {"fx": 2.0},
    }
]


@pytest.mark.parametrize(
    "dict_dummy, expected",
    [
        (SETUP_IN[0], SETUP_OUT[0]),
    ],
)
def test_setup(dict_dummy, expected):
    service = component_api.ComponentService()
    message = Struct()
    message.update(dict_dummy)
    request = ComponentRequest(inputs=message)
    response = service.Setup(request, context=None)
    data = json_format.MessageToDict(response.outputs)
    assert data == expected


@pytest.mark.parametrize(
    "dict_dummy, expected",
    [
        (SETUP_OUT[0], COMPUTE_OUT[0]),
    ],
)
def test_compute(dict_dummy, expected):
    service = component_api.ComponentService()
    message = Struct()
    message.update(dict_dummy)
    request = ComponentRequest(inputs=message)
    response = service.Compute(request, context=None)
    data = json_format.MessageToDict(response.outputs)
    assert data == expected


@pytest.mark.parametrize(
    "dict_dummy, expected",
    [
        (SETUP_IN[0], SETUP_OUT[0]),
    ],
)
def test_setup_api(dict_dummy, expected, name="adder"):
    """Emulate the client call to the component.
    Warning: component needs to be running!!!
    """
    message = Struct()
    message.update(dict_dummy)
    request = ComponentRequest(inputs=message)

    channel = grpc.insecure_channel(f"localhost:{component_api.PORT}")
    client = ComponentStub(channel)

    response = client.Setup(request)
    data = json_format.MessageToDict(response.outputs)
    assert data == expected


@pytest.mark.parametrize(
    "dict_dummy, expected",
    [
        (SETUP_OUT[0], COMPUTE_OUT[0]),
    ],
)
def test_compute_api(dict_dummy, expected, name="adder"):
    """Emulate the client call to the component.
    Warning: component needs to be running!!!
    """
    message = Struct()
    message.update(dict_dummy)
    request = ComponentRequest(inputs=message)

    channel = grpc.insecure_channel(f"localhost:{component_api.PORT}")
    client = ComponentStub(channel)

    response = client.Compute(request)
    data = json_format.MessageToDict(response.outputs)
    assert data == expected


def test_get_input_files():
    get_input_files(ufpath=USER_FILES_PATH, be_api=BE_API_HOST, comp=COMP_NAME)


def test_install():
    log_text = install("editables/requirements.txt", my_pypi=MYPYPI_HOST)
    assert "Collecting numpy" in log_text
    assert "Installing collected packages: numpy" in log_text
    assert "Successfully installed numpy-" in log_text
    # cleanup
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "numpy", "-y"])
