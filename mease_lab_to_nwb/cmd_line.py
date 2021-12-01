from nwb_web_gui import init_app
from pathlib import Path
from threading import Timer
import webbrowser
import os


# ----------------   EDIT HERE  ---------------------------
# GUI options
NWB_GUI_RENDER_CONVERTER = "True"
NWB_GUI_RENDER_VIEWER = "True"
NWB_GUI_RENDER_DASHBOARD = "False"

# Converter module and class
NWB_GUI_CONVERTER_MODULE = "mease_lab_to_nwb"
NWB_GUI_CONVERTER_CLASS = dict(ced="CEDNWBConverter", syntalos="SyntalosNWBConverter")
# ---------------------------------------------------------

experiments_text = ", ".join([i for i in NWB_GUI_CONVERTER_CLASS.keys()])


def parse_arguments():
    f"""
    Command line shortcut to open GUI editor.
    Usage:
    $ nwbgui-mease [experiment] [--data_path] [--port]

    experiment : str
        The name of the specfic experiment.
        Options: {experiments_text}
    data_path : str
        Optional. Base path to experimental data.
    port : int
        Optional. Port where app will be running.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="NWB converter GUI, with automatic metadata fetching.",
    )

    parser.add_argument(
        "experiment",
        help=f"The name of the specfic experiment. Options: {experiments_text}",
    )
    parser.add_argument(
        "--data_path",
        default=".",
        help="Path to datasets. Defaults to current working directory.",
    )
    parser.add_argument(
        "--port",
        default="5000",
        help="Port where app will be running. Defaults to 5000.",
    )
    parser.add_argument(
        "--dev", default=False, help="Run in development mode. Defaults to False."
    )

    # Parse arguments
    args = parser.parse_args()

    return args


def cmd_line_shortcut():
    run_args = parse_arguments()

    # Set ENV variables for app
    data_path = str(Path(run_args.data_path))
    os.environ["NWB_GUI_ROOT_PATH"] = data_path
    os.environ["NWB_GUI_RENDER_CONVERTER"] = NWB_GUI_RENDER_CONVERTER
    os.environ["NWB_GUI_RENDER_VIEWER"] = NWB_GUI_RENDER_VIEWER
    os.environ["NWB_GUI_RENDER_DASHBOARD"] = NWB_GUI_RENDER_DASHBOARD
    os.environ["FLASK_ENV"] = "production"

    # Choose converter
    os.environ["NWB_GUI_CONVERTER_MODULE"] = NWB_GUI_CONVERTER_MODULE
    os.environ["NWB_GUI_CONVERTER_CLASS"] = NWB_GUI_CONVERTER_CLASS[run_args.experiment]

    print(f"NWB GUI running on localhost:{run_args.port}")
    print(f"Data path: {data_path}")
    if run_args.dev:
        os.environ["FLASK_ENV"] = "development"
        print("Running in development mode")

    # Initialize app
    app = init_app()

    # Open browser after 1 sec
    def open_browser():
        webbrowser.open_new(f"http://localhost:{run_args.port}/")

    Timer(1, open_browser).start()

    # Run app
    app.run(
        host="0.0.0.0",
        port=run_args.port,
        debug=run_args.dev,
        use_reloader=run_args.dev,
    )
