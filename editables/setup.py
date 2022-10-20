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

from functools import reduce
from operator import getitem
from datetime import datetime


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    params: dict = None,
):
    """Editable setup function."""

    # set default inputs
    if inputs:
        for input_key, input_value in inputs.items():
            if input_value == "default":
                tree = input_key.split(".")
                try:
                    inputs[input_key] = getFromDict(params, tree)
                except Exception as e:
                    print(f"Could not find {input_key} in the input parameters.")

    # initiate output values
    if outputs:
        for output in outputs:
            outputs[output] = 0.0

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."

    return {"message": message, "inputs": inputs, "outputs": outputs}


def getFromDict(dataDict: dict, mapList: list):
    """Traverse a dictionary and get value by providing a list of keys."""
    return reduce(getitem, mapList, dataDict)
