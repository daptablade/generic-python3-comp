from datetime import datetime
from pathlib import Path


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    params: dict = None,
    run_folder: Path = None,
    inputs_folder: Path = None,
):
    """Editable setup function."""

    # initalise setup_data keys
    response = {}

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."
    print(message)
    response["message"] = message

    return response
