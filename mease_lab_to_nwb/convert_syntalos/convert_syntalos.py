"""Authors: Alessio Buccino, Cody Baker, Szonja Weigl, and Ben Dichter."""
from pathlib import Path

from .syntalosnwbconverter import SyntalosNWBConverter

base_path = Path("D:/Syntalos/Latest Syntalos Recording _20200730")
intan_folder_path = base_path / "intan-signals"
event_file_path = base_path / "events" / "table.csv"
video_folder_path = base_path / "videos" / "TIS Camera"
nwbfile_path = base_path / "Syntalos_stub.nwb"

stub_test = True
use_tsync_timestamps = True


# Automatically performs conversion based on above filepaths and options
source_data = dict(
    SyntalosEvent=dict(file_path=str(event_file_path.absolute())),
    SyntalosImage=dict(folder_path=str(video_folder_path.absolute())),
    SyntalosRecording=dict(folder_path=str(intan_folder_path.absolute()))
)
conversion_options = dict(
    SyntalosEvent=dict(use_timestamps=use_tsync_timestamps),
    SyntalosImage=dict(use_timestamps=use_tsync_timestamps),
    SyntalosRecording=dict(stub_test=stub_test, use_timestamps=use_tsync_timestamps)
)
converter = SyntalosNWBConverter(source_data)
metadata = converter.get_metadata()
converter.run_conversion(
    nwbfile_path=str(nwbfile_path.absolute()),
    metadata=metadata,
    conversion_options=conversion_options
)
