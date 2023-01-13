from datetime import datetime
from time import sleep


def compute(
    inputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    outputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    partials: dict = {},
    options: dict = {},
    parameters: dict = {
        "user_input_files": [],
        "inputs_folder_path": "",
        "outputs_folder_path": "",
    },
) -> dict:

    """Editable compute function."""

    # execute the workflow
    sleep(1)

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Adder compute completed."
    print(message)

    return {"message": message}
