"""Authors: Alessio Buccino, Cody Baker, Szonja Weigl, and Ben Dichter."""
from pathlib import Path

from .syntalosnwbconverter import SyntalosNWBConverter


base_path = Path("D:/Syntalos/Latest Syntalos Recording _20200730")
# originally, this intan file had a -002 attached to the end before the .rhd, but spikeextractors complained
intan_file_path = base_path / "intan-signals" / "169d_data_200714_121455.rhd"
event_file_path = base_path / "events" / "table.csv"
video_folder_path = base_path / "videos" / "TIS Camera"
nwbfile_path = base_path / "Syntalos_stub.nwb"

if base_path.is_dir():
    input_args = dict(
        IntanRecording=dict(
            file_path=intan_file_path
        )
    )

    converter = SyntalosNWBConverter(**input_args)
    metadata = converter.get_metadata()

    # Session specific metadata
    metadata['NWBFile'].update(session_description="Session description.")

    converter.run_conversion(
        nwbfile_path=str(nwbfile_path.absolute()),
        metadata_dict=metadata,
        stub_test=True
    )
