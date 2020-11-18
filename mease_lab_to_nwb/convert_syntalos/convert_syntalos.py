"""Authors: Alessio Buccino, Cody Baker, Szonja Weigl, and Ben Dichter."""
from pathlib import Path

from .syntalosnwbconverter import SyntalosNWBConverter

base_path = Path("D:/Syntalos/Latest Syntalos Recording _20200730")
intan_file_path = base_path / "intan-signals" / "169d_data_200714_121455.rhd"
event_file_path = base_path / "events" / "table.csv"
video_folder_path = base_path / "videos" / "TIS Camera"
nwbfile_path = base_path / "Syntalos_stub.nwb"

if base_path.is_dir():
    input_args = dict(
        SyntalosEvent=dict(file_path=str(event_file_path.absolute())),
        SyntalosImage=dict(folder_path=str(video_folder_path.absolute())),
        IntanRecording=dict(file_path=str(intan_file_path.absolute()), dtype="uint16")
    )
    conversion_options = dict(
        IntanRecording=dict(stub_test=True)
    )

    converter = SyntalosNWBConverter(**input_args)
    metadata = converter.get_metadata()
    converter.run_conversion(
        nwbfile_path=str(nwbfile_path.absolute()),
        metadata=metadata,
        conversion_options=conversion_options
    )
