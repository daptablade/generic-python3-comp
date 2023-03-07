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

from concurrent import futures
from signal import signal, SIGTERM
import json
import grpc
import threading

from google.protobuf.struct_pb2 import Struct
from google.protobuf import json_format

from component_pb2 import ComponentResponse, ComponentLargeMessage
import component_pb2_grpc

from component import setup, compute, COMP_NAME

PORT = 50060
LOCK = threading.Lock()


class ComponentService(component_pb2_grpc.ComponentServicer):
    """main class of the app."""

    # this method must have the same name as the RPC you define in your protobuf file
    def Setup(self, request, context):
        with LOCK:
            print("received setup request")
            try:
                (msg, outputs) = setup(**json_format.MessageToDict(request.inputs))
            except Exception as e:
                print(e)
                raise e
            return ComponentResponse(outputmsg=msg, outputs=get_msg_body(outputs))

    def Compute(self, request, context):
        with LOCK:
            print("received small compute request")
            try:
                (msg, outputs) = compute(**json_format.MessageToDict(request.inputs))
                return ComponentResponse(outputmsg=msg, outputs=get_msg_body(outputs))
            except Exception as e:
                print(e)
                raise e

    def LargeCompute(self, request_iterator, context):
        """Method with stream of json strings for request and response."""
        with LOCK:
            print("received large compute request")
            try:
                inputs = message_to_dict(request_iterator)
                yield from dict_to_message(compute(**inputs))
            except Exception as e:
                print(e)
                raise e


def get_msg_body(outputs):
    message_body = Struct()
    message_body.update(outputs)
    return message_body


def dict_to_message(data, step=100000):
    # data dictionary to json
    json_object = json.dumps(data, indent=None)
    # json string to chunks
    for ii in range(0, len(json_object), step):
        yield ComponentLargeMessage(jsonstr=json_object[ii : ii + step])


def message_to_dict(message) -> dict:
    return json.loads("".join([val.jsonstr for val in message]))


def serve(service):
    """Starts a network server and uses your microservice class to handle requests."""

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    component_pb2_grpc.add_ComponentServicer_to_server(service, server)
    server.add_insecure_port(f"[::]:{PORT}")
    server.start()

    def handle_sigterm(*_):
        print(f"Component {COMP_NAME} received shutdown signal")
        all_rpcs_done_event = server.stop(30)
        all_rpcs_done_event.wait(30)
        print(f"Component {COMP_NAME} shut down gracefully")

    signal(SIGTERM, handle_sigterm)

    server.wait_for_termination()


if __name__ == "__main__":
    serve(ComponentService())
