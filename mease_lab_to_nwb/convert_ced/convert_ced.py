"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path

from mease_lab_to_nwb import CEDNWBConverter


base_path = Path("D:/CED_example_data/Other example")
ced_file_path = base_path / "m365_pt1_590-1190secs-001.smrx"
nwbfile_path = base_path / "CED_stub.nwb"

source_data = dict(
    CEDRecording=dict(
        file_path=str(ced_file_path.absolute())
    )
)
conversion_options = dict(
    CEDRecording=dict(stub_test=True)
)

converter = CEDNWBConverter(source_data)
metadata = converter.get_metadata()
converter.run_conversion(
    nwbfile_path=str(nwbfile_path),
    metadata=metadata,
    conversion_options=conversion_options
)
