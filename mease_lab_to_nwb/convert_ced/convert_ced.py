"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
from spikeextractors import CEDRecordingExtractor

from cednwbconverter import CEDNWBConverter


base_path = Path("D:/CED_example_data/Short example")
ced_file_path = base_path / "M113_C4.smrx"
# base_path = Path("D:/CED_example_data/Other example")
# ced_file_path = base_path / "m365_pt1_590-1190secs-001.smrx"
nwbfile_path = base_path / "CED_stub.nwb"

from datetime import datetime
session_start_time = datetime(2000,1,1)

channel_info = CEDRecordingExtractor.get_all_channels_info(ced_file_path)

rhd_channels = []
for ch, info in channel_info.items():
    if "Rhd" in info["title"]:
        rhd_channels.append(ch)

source_data = dict(
    CEDRecording=dict(
        file_path=str(ced_file_path.absolute()),
        smrx_ch_inds=rhd_channels
    )
)
conversion_options = dict(
    CEDRecording=dict(stub_test=True)
)

converter = CEDNWBConverter(source_data)
metadata = converter.get_metadata()
metadata['NWBFile'].update(session_start_time=session_start_time)
converter.run_conversion(
    nwbfile_path=str(nwbfile_path.absolute()),
    metadata=metadata,
    conversion_options=conversion_options
)
