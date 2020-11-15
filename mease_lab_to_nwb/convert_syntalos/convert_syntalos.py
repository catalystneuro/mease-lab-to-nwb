"""Authors: Alessio Buccino, Cody Baker, Szonja Weigl, and Ben Dichter."""
from pathlib import Path

from syntalosnwbconverter import SyntalosNWBConverter


base_path = Path("D:/Syntalos/Latest Syntalos Recording _20200730")
# originally, this intan file had a -002 attached to the end before the .rhd, but spikeextractors complained
intan_file_path = base_path / "intan-signals" / "169d_data_200714_121455.rhd"
event_file_path = base_path / "events" / "table.csv"
video_folder_path = base_path / "videos" / "TIS Camera"
nwbfile_path = base_path / "Syntalos_stub.nwb"

if base_path.is_dir():
    input_args = dict(
        SyntalosEvent=dict(file_path=event_file_path),
        SyntalosImage=dict(folder_path=video_folder_path),
        IntanRecording=dict(file_path=intan_file_path, dtype="uint16")
    )
    
    conversion_options = dict(
        SyntalosEvent=dict(),
        SyntalosImage=dict(),
        IntanRecording=dict(stub_test=True)
    )
    converter = SyntalosNWBConverter(**input_args)
    metadata = converter.get_metadata()
    converter.run_conversion(nwbfile_path=str(nwbfile_path.absolute()), metadata_dict=metadata, **conversion_options)
