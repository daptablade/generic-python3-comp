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

from datetime import datetime
from component_api2 import call_compute


def compute(
    setup_data: dict = None,
    params: dict = None,
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
    root_folder: str = None,
):

    """Editable compute function."""

    print("Starting compute with setup data: ", setup_data)
    x = float(setup_data["x"])
    f = setup_data["f"]
    times = int(setup_data["times"])

    # set outputs
    outputs = repeat(f=f, x=x, times=times)
    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Adder compute completed."
    print(message)

    return {"message": message, "outputs": outputs}


def repeat(f="lambda x: x+1", x=0.0, times=10):
    alliterations = []
    print("starting repeat...")
    for i in range(times):
        if "lambda x: x+1" == f:  # for testing
            f_local = lambda x: x + 1
            x = f_local(x)
            alliterations.append(x)
        else:
            print("start iteration # ", i + 1)
            (_, data) = call_compute(
                {
                    "component": f,
                    "inputs": {"x": x},
                    "get_grads": False,
                    "get_outputs": True,
                }
            )
            print("call compute returns: ", data)
            x = data["outputs"]["fx"]
            print("x = ", x)
            alliterations.append(x)
    return {"all_iterations": alliterations}
