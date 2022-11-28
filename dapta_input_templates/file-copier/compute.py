from datetime import datetime
from pathlib import Path
import shutil


def compute(
    setup_data: dict = None,
    params: dict = None,
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
    run_folder: Path = None,
    inputs_folder: Path = None,
):

    """Editable compute function."""

    print("Starting user function evaluation.")
    component_inputs = params  # default values

    for file in setup_data["user_input_files"]:
        src = inputs_folder / file
        shutil.copy(src, run_folder / (src.stem + "_out" + src.suffix))

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Copied files."
    print(message)

    return {"message": message}
