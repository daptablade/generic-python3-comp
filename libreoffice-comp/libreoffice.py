import sys

sys.path.append("/usr/bin/libreoffice/program")

import os
import uno
from com.sun.star.beans import PropertyValue
import datetime
from pathlib import Path


def PythonVersion(model):
    """Prints the Python version into the current document"""
    # # get the doc from the scripting context which is made available to all scripts
    # desktop = XSCRIPTCONTEXT.getDesktop()
    # model = desktop.getCurrentComponent()
    # # check whether there's already an opened document. Otherwise, create a new one
    # if not hasattr(model, "Sheets"):
    #     model = desktop.loadComponentFromURL("private:factory/scalc", "_blank", 0, ())

    # get the XText interface
    sheet = model.Sheets.getByIndex(0)
    # create an XTextRange at the end of the document
    tRange = sheet.getCellRangeByName("C4")
    # and set the string
    now = datetime.datetime.now()
    tRange.String = (
        "The Python version is %s.%s.%s" % sys.version_info[:3]
        + f"\n timestamp: {now.strftime('%d/%m/%Y, %H:%M:%S')}"
    )
    # do the same for the python executable path
    tRange = sheet.getCellRangeByName("C5")
    tRange.String = sys.executable

    return model


def store(model, file=None):
    # store the document
    path = uno.systemPathToFileUrl(file)
    try:
        model.storeAsURL(path, ())
    except Exception:
        properties = []
        p = PropertyValue()
        properties.append(p)
        model.storeToURL(path, tuple(properties))
    return None


def get_model():
    # Start libreoffice in headless mode
    os.system(
        '/usr/bin/libreoffice --headless --nologo --nofirststartwizard --accept="socket,host=0.0.0.0,port=8100;urp" &'
    )
    desktop = get_desktop()
    # create blank spreadsheet
    model = desktop.loadComponentFromURL("private:factory/scalc", "_blank", 0, ())
    return model


def open_file(path):
    desktop = get_desktop()
    path = uno.systemPathToFileUrl(path)
    props_dict = {
        "AsTemplate": False,
        "MacroExecutionMode": 4,  # ALWAYS_EXECUTE_NO_WARN
    }
    properties = []
    for key, val in props_dict.items():
        p = PropertyValue()
        p.Name = key
        p.Value = val
        properties.append(p)
    model = desktop.loadComponentFromURL(path, "_default", 0, tuple(properties))
    return model


def get_current_file():
    desktop = get_desktop()
    model = desktop.getCurrentComponent()
    return model


def get_desktop():
    # Get local context info
    localContext = uno.getComponentContext()
    resolver = localContext.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", localContext
    )

    ctx = None
    # Wait until the OpenOffice starts and connection is established
    while ctx == None:
        try:
            ctx = resolver.resolve(
                "uno:socket,host=localhost,port=8100;urp;StarOffice.ComponentContext"
            )
            smgr = ctx.ServiceManager
        except:
            pass

    # get the central desktop object
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    return desktop


if __name__ == "__main__":

    # connect
    model = get_model()

    # Trigger our job
    model = PythonVersion(model)
    store(model, file="")
