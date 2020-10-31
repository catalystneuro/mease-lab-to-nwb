"""Authors: Cody Baker and Ben Dichter."""
# TODO: add pathlib
import os

from joblib import Parallel, delayed

from mease_lab_to_nwb import SyntalosNWBConverter

n_jobs = 1  # number of parallel streams to run

# TODO: Need to update base_path
base_path = "D:/Heidelberg_data/CED_example_data"

# Manual list of selected sessions that cause problems with the general functionality
exlude_sessions = []

virmen_session_strings = []
spikeglx_session_strings = []
nwbfile_paths = []
for j, (virmen_session, spikeglx_session) in enumerate(zip(virmen_session_strings, spikeglx_session_strings)):
    virmen_session_strings[j] = os.path.join(base_path, virmen_session_strings[j])
    spikeglx_session_strings[j] = os.path.join(base_path, spikeglx_session_strings[j])
    nwbfile_paths.append(os.path.join(base_path, virmen_session) + "_local_stub.nwb")  # name defaults to virmen session


def run_syntalos_conv(virmen_session, spikeglx_session, nwbfile_path):
    """Conversion function to be run in parallel."""
    if os.path.exists(base_path):
        print(f"Processsing {virmen_session}...")
        if not os.path.isfile(nwbfile_path):
            input_args = dict(
                SpikeGLXRecording=dict(file_path=spikeglx_session+".imec0.ap.bin"),
                TowersPosition=dict(folder_path=virmen_session)
            )

            converter = SyntalosNWBConverter(**input_args)
            metadata = converter.get_metadata()

            # Session specific metadata
            metadata['NWBFile'].update(session_description="")

            # metadata[yuta_converter.get_recording_type()]['Ecephys']['Device'][0].update({'name': 'implant'})

            # for electrode_group_metadata in \
            #         metadata[yuta_converter.get_recording_type()]['Ecephys']['ElectrodeGroup']:
            #     electrode_group_metadata.update({'location': 'unknown'})
            #     electrode_group_metadata.update({'device_name': 'implant'})

            converter.run_conversion(nwbfile_path=nwbfile_path, metadata_dict=metadata, stub_test=True)
    else:
        print(f"The folder ({base_path}) does not exist!")


Parallel(n_jobs=n_jobs)(delayed(run_syntalos_conv)(virmen_session, spikeglx_session, nwbfile_path)
                        for virmen_session, spikeglx_session, nwbfile_path
                        in zip(virmen_session_strings, spikeglx_session_strings, nwbfile_paths)
                        if os.path.split(virmen_session)[1] not in exlude_sessions)
