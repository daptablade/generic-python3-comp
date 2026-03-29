import os
from datetime import datetime
from pathlib import Path
import glob
import zipfile
from contextlib import redirect_stdout

import shutil
import pathlib
import pdb
import sys
import jax.numpy as jnp
import feniax.preprocessor.configuration as configuration  # import Config, dump_to_yaml
from feniax.preprocessor.inputs import Inputs
import feniax.feniax_main

# RUN CASES
import time

TIMES_DICT = dict()
SOL = dict()
CONFIG = dict()


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

    run_folder = Path(parameters["outputs_folder_path"])

    with open(
        run_folder / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_feniax.log",
        "w",
        encoding="utf-8",
    ) as f:
        with redirect_stdout(f):
            print("Starting user function evaluation.")

            cwd = os.getcwd()
            os.chdir(run_folder)

            # delete previous results
            output_zip = run_folder / "output_files.zip"
            if output_zip.is_file():
                shutil.rmtree(output_zip)

            examples_path = feniax.PATH / "../examples"
            SP_folder = examples_path / "SailPlane"

            # create results folders
            os.mkdir("./results")

            inp = Inputs()
            inp.log.level = "debug"
            inp.engine = "intrinsicmodal"
            inp.fem.eig_type = "inputs"
            inp.fem.connectivity = dict(
                FuselageFront=["RWingInner", "LWingInner"],
                FuselageBack=["BottomTail", "Fin"],
                RWingInner=["RWingOuter"],
                RWingOuter=None,
                LWingInner=["LWingOuter"],
                LWingOuter=None,
                BottomTail=["LHorizontalStabilizer", "RHorizontalStabilizer"],
                RHorizontalStabilizer=None,
                LHorizontalStabilizer=None,
                Fin=None,
            )

            inp.fem.folder = SP_folder / "FEM/"
            inp.fem.num_modes = 50
            inp.driver.typeof = "intrinsic"

            # inp.driver.sol_path = pathlib.Path(
            #    f"./results_{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}")
            inp.driver.sol_path = run_folder / "results"
            inp.simulation.typeof = "single"
            inp.systems.sett.s1.solution = "static"
            inp.systems.sett.s1.solver_library = "diffrax"
            inp.systems.sett.s1.solver_function = "newton"
            inp.systems.sett.s1.solver_settings = dict(
                rtol=1e-6, atol=1e-6, max_steps=50, norm="linalg_norm", kappa=0.01
            )
            # inp.systems.sett.s1.solver_library = "scipy"
            # inp.systems.sett.s1.solver_function = "root"
            # inp.systems.sett.s1.solver_settings = dict(method='hybr',#'krylov',
            #                                           tolerance=1e-9)
            # inp.systems.sett.s1.label = 'dq_001001'
            inp.systems.sett.s1.xloads.follower_forces = True
            inp.systems.sett.s1.xloads.follower_points = [[25, 2], [48, 2]]

            inp.systems.sett.s1.xloads.x = [0, 1, 2, 3, 4, 5, 6]
            inp.systems.sett.s1.xloads.follower_interpolation = [
                [0.0, 2e5, 2.5e5, 3.0e5, 4.0e5, 4.8e5, 5.3e5],
                [0.0, 2e5, 2.5e5, 3.0e5, 4.0e5, 4.8e5, 5.3e5],
            ]
            inp.systems.sett.s1.t = [1, 2, 3, 4, 5, 6]

            # config =  configuration.Config(inp)

            # path2config = pathlib.Path("./config.yaml")
            config = configuration.Config(inp)
            # configuration.dump_to_yaml(path2config, config, with_comments=True)

            sol = feniax.feniax_main.main(input_obj=config)

            os.chdir(cwd)

            # zip all data in outputs folder to be able to recover it with structure
            result_files = [
                Path(f)
                for f in glob.glob("**/*.*", recursive=True, root_dir=run_folder)
            ]
            with zipfile.ZipFile(output_zip, mode="w") as archive:
                for file in result_files:
                    if not (run_folder / file).is_file():
                        raise FileNotFoundError(f"Cannot find output file {file}")
                    archive.write(run_folder / file, arcname=file)
            shutil.rmtree(run_folder / "results")

            message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Completed compute."
            print(message)

    return {"message": message, "outputs": outputs}
