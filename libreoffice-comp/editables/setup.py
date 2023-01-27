from datetime import datetime
from pathlib import Path

from libreoffice import get_model, store, start_libreoffice
from com.sun.star.awt.FontWeight import BOLD, NORMAL


def setup(
    inputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    outputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    parameters: dict = {
        "user_input_files": [],
        "inputs_folder_path": "",
        "outputs_folder_path": "",
    },
) -> dict:
    """A user editable setup function.

    Parameters
    ----------
    inputs: dict
        The component Inputs sorted by type (design, implicit or setup).
    outputs: dict
        The component Outputs sorted by type (design, implicit or setup).
    parameters: dict
        The component Parameters as defined in the component 'Parameters' tab.
        Includes the following special keys:
        'user_input_files': list of user-uploaded input file filenames
        'inputs_folder_path': path to all user and connection input files (str)
        'outputs_folder_path': path to component outputs folder (str)

    Returns
    -------
    dict
        dictionary of JSON-serialisable keys and values, including:
        inputs: dict, optional
            The setup function can assign values to input keys, but the inputs
            keys should not be modified.
        outputs: dict, optional
            The setup function can assign values to output keys, but the outputs
            keys should not be modified.
        parameters: dict, optional
            The setup function can add key/value pairs to the parameters dict,
            but the existing key/value pairs cannot be modified.
        partials: dict, optional
            The derivatives of the component's "design" outputs with respect to its
            "design" inputs, used for gradient-based design optimisation Runs.
        message: str, optional
            A setup message that will appear in the Run log.
    """

    run_folder = Path(parameters["outputs_folder_path"])

    # start libreoffice and get a blank spreadsheet
    start_libreoffice()
    model = get_model()

    # add data titles
    if not "column_names" in parameters:
        parameters["column_names"] = ["x", "y", "f(x,y)"]
    model = set_column_titles(model, parameters["column_names"])

    # save spreadsheet
    now = datetime.now()
    full_path = run_folder.resolve()
    file = str(full_path / ("calc_" + now.strftime("%Y-%m-%d_%H-%M-%S") + ".ods"))
    store(model, file)
    # add filepath to the parameters
    parameters["ods_file"] = file
    model.close(True)

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."
    print(message)

    return {"message": message, "parameters": parameters}


def set_column_titles(model, titles):
    sheet = model.Sheets.getByIndex(0)
    cells = sheet[0, :]
    cells.setPropertyValue("CharWeight", BOLD)

    for ii, title in enumerate(titles):
        sheet[0, ii].String = title
    return model
