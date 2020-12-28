"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
from datetime import datetime
from isodate import duration_isoformat
from datetime import timedelta

from mease_lab_to_nwb import CEDNWBConverter


base_path = Path("D:/CED_example_data/Other example")
ced_file_path = base_path / "m365_pt1_590-1190secs-001.smrx"
nwbfile_path = base_path / "CED_stub.nwb"

# Enter Session and Subject information here
session_description = "Enter session description here."

# Manually insert the session start time
session_start = datetime(1971, 1, 1, 1, 1, 1)  # (Year, Month, Day, Hour, Minute, Second)

# Uncomment any subject fields you want to include
subject_info = dict(
    subject_id="Enter optional subject id here",
    # description="Enter optional subject description here",
    # weight="Enter subject weight here",
    # age=duration_isoformat(timedelta(days=0)),  # Enter the age of the subject in days
    # species="Mus musculus",
    # genotype="Enter subject genotype here",
    # sex="Enter subject sex here"
)

# Set some global conversion options here
stub_test = True
overwrite = True  # If the NWBFile exists at the path, replace it; otherwise it will append


# Automatically performs conversion based on above filepaths and options
source_data = dict(
    CEDRecording=dict(file_path=str(ced_file_path)),
    CEDStimulus=dict(file_path=str(ced_file_path))
)
conversion_options = dict(
    CEDRecording=dict(stub_test=stub_test),
    CEDStimulus=dict(stub_test=stub_test)
)
converter = CEDNWBConverter(source_data)
metadata = converter.get_metadata()
metadata['NWBFile'].update(session_description=session_description, session_start_time=session_start.astimezone())
metadata.update(Subject=subject_info)
converter.run_conversion(
    nwbfile_path=str(nwbfile_path),
    metadata=metadata,
    conversion_options=conversion_options,
    overwrite=overwrite
)
