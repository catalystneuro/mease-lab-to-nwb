"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path

from .cednwbconverter import CEDNWBConverter

n_jobs = 1  # number of parallel streams to run

base_path = Path("D:/CED_example_data")
ced_file_path = base_path / "m365_pt1_590-1190secs-001.smrx"
nwbfile_path = base_path / "CED_stub.nwb"

# Manual list of selected sessions that cause problems with the general functionality
exlude_sessions = []
nwbfile_paths = []


if base_path.is_dir():
    source_data = dict(
        CEDRecording=dict(file_path=str(ced_file_path.absolute()), dtype="uint16")
    )
    conversion_options = dict(
        CEDRecording=dict(stub_test=True)
    )

    converter = CEDNWBConverter(source_data)
    metadata = converter.get_metadata()
    converter.run_conversion(
        nwbfile_path=str(nwbfile_path.absolute()),
        metadata=metadata,
        conversion_options=conversion_options
    )
