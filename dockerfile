FROM python:3.8

RUN mkdir /app
COPY protobufs /app/protobufs
COPY generic_python3_comp/editables /app/generic_python3_comp/editables
COPY generic_python3_comp/component.py /app/generic_python3_comp/
COPY generic_python3_comp/component_api.py /app/generic_python3_comp/
COPY generic_python3_comp/utils.py /app/generic_python3_comp/
COPY generic_python3_comp/requirements.txt /app/generic_python3_comp/
COPY generic_python3_comp/README.md /app/generic_python3_comp/
COPY generic_python3_comp/VERSION /app/generic_python3_comp/
WORKDIR /app/generic_python3_comp

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt
RUN python -m grpc_tools.protoc -I ../protobufs --python_out=. --grpc_python_out=. ../protobufs/component.proto

EXPOSE 50060
ENTRYPOINT [ "python", "component_api.py" ]