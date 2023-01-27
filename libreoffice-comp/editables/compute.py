from datetime import datetime
from pathlib import Path

import uno
from libreoffice import store, get_current_file


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

    inputs_folder = Path(parameters["inputs_folder_path"])
    run_folder = Path(parameters["outputs_folder_path"])

    # open saved spreadsheet
    model = get_current_file()

    # add data and plot
    if not inputs["design"]:
        inputs["design"] = {"x": [0, 1, 2], "y": [1, 2, 3], "f(x,y)": [1, 3, 5]}
    model = set_values(model, inputs["design"])

    # save spreadsheet
    store(model, parameters["ods_file"])

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Saved ODS spreadsheet."
    print(message)

    return {"message": message}


def set_values(model, data):
    sheet = model.Sheets.getByIndex(0)
    jj = 0
    for title, value in data.items():
        while True:
            if title == sheet[0, jj].String:
                break
            else:
                jj += 1
        for ii, val in enumerate(value):
            sheet[ii + 1, jj].Value = val

    range_address = sheet.getCellRangeByPosition(
        0, 0, len(data) - 1, ii + 1
    ).getRangeAddress()

    plot_data(sheet, name="data", range_address=range_address)

    return model


def plot_data(sheet, name, range_address):

    rect = uno.createUnoStruct("com.sun.star.awt.Rectangle")
    rect.Width, rect.Height, rect.X, rect.Y = 22000, 12000, 1000, 9200

    oCharts = sheet.getCharts()

    # first bool: ColumnHeaders
    # second bool: RowHeaders
    oCharts.addNewByName(name, rect, (range_address,), True, False)
    chart = oCharts.getByName(name).getEmbeddedObject()
    chart.createInstance("com.sun.star.chart.LineDiagram")

    chart.HasMainTitle = True
    chart.HasLegend = True
    chart.Title.String = name
    chart.Title.CharHeight = 24
    chart.HasSubTitle = False

    diagram = chart.getDiagram()
