"""Authors: Cody Baker and Ben Dichter."""
# TODO: add pathlib
import os

from joblib import Parallel, delayed

from mease_lab_to_nwb import CEDNWBConverter

n_jobs = 1  # number of parallel streams to run

base_path = "D:/Heidelberg_data/CED_example_data"

# Manual list of selected sessions that cause problems with the general functionality
exlude_sessions = []
nwbfile_paths = []


def run_ced_conv(virmen_session, spikeglx_session, nwbfile_path):
    """Conversion function to be run in parallel."""
    if os.path.exists(base_path):
        print(f"Processsing {virmen_session}...")
        if not os.path.isfile(nwbfile_path):

            converter = CEDNWBConverter(**input_args)
            metadata = converter.get_metadata()

            converter.run_conversion(nwbfile_path=nwbfile_path, metadata_dict=metadata, stub_test=True)
    else:
        print(f"The folder ({base_path}) does not exist!")

