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
import grpc
from google.protobuf.struct_pb2 import Struct
from google.protobuf import json_format

import json
from orchestrator_pb2_grpc import OrchestratorStub
from component_pb2 import ComponentRequest

orchestrator_host = os.getenv("ORCHESTRATOR_HOST", "localhost:50051")
assert orchestrator_host, "env var ORCHESTRATOR_HOST should be set to host:port"

orchestrator_channel = grpc.insecure_channel(orchestrator_host)
orchestrator_client = OrchestratorStub(orchestrator_channel)


def default_call(method, message_body):
    # from dictionary to gRPC protobuf structure
    message = Struct()
    message.update(message_body)

    # send request to component
    request = ComponentRequest(inputs=message)
    response = method(request)

    # parse the response object
    msg = response.outputmsg
    data = json_format.MessageToDict(response.outputs)

    return (msg, data)


def stream_call(method, message_body):
    response = method(dict_to_message(message_body), None)
    data = message_to_dict(response)
    return data


def call_compute(message_body, stream_messages=False):
    if not stream_messages:
        return default_call(orchestrator_client.CallCompute, message_body)
    else:
        return stream_call(orchestrator_client.CallLargeCompute, message_body)


def call_setup(message_body):
    return default_call(orchestrator_client.GetCompAttributes, message_body)


def dict_to_message(data: dict, step=100000):
    # data dictionary to json
    json_object = json.dumps(data, indent=None)
    # json string to chunks
    for ii in range(0, len(json_object), step):
        yield ComponentLargeMessage(jsonstr=json_object[ii : ii + step])


def message_to_dict(message) -> dict:
    return json.loads("".join([val.jsonstr for val in message]))
