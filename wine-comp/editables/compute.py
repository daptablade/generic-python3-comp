from datetime import datetime
from pathlib import Path

from helloworld import execute_helloworld


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
    """A user editable compute function.

    Here the compute function copies input files to the output folder.

    Parameters
    ----------
    inputs: dict
        The component Inputs sorted by type (design, implicit or setup).
    outputs: dict
        The component Outputs sorted by type (design, implicit or setup).
    partials: dict, optional
        The derivatives of the component's "design" outputs with respect to its
        "design" inputs, used for gradient-based design optimisation Runs.
    options: dict, optional
        component data processing options and flags, inc. : "stream_call",
        "get_outputs", "get_grads"
    parameters: dict
        The component Parameters as returned by the setup function.

    Returns
    -------
    dict
        dictionary of JSON-serialisable keys and values, including:
        outputs: dict, optional
            The compute function can assign values to output keys, but the outputs
            keys should not be modified.
        partials: dict, optional
            The compute function can assign values to partials keys, but the
            partials keys should not be modified.
        message: str, optional
            A compute message that will appear in the Run log.
    """

    print("Starting user function evaluation.")

    run_folder = Path(parameters["outputs_folder_path"])
    execute_helloworld(run_folder)

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: helloworld.exe has been executed and output saved in helloworld.out."
    print(message)

    return {"message": message}
