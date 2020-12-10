"""Authors: Alessio Buccino, Cody Baker, Szonja Weigl, and Ben Dichter."""
from pathlib import Path
from isodate import duration_isoformat
from datetime import timedelta

from mease_lab_to_nwb import SyntalosNWBConverter

base_path = Path("D:/Syntalos/Latest Syntalos Recording _20200730")
intan_folder_path = base_path / "intan-signals"
event_file_path = base_path / "events" / "table.csv"
video_folder_path = base_path / "videos" / "TIS Camera"
nwbfile_path = base_path / "Syntalos.nwb"

# Enter Session and Subject information here
# Comment out or remove any fields you do not want to include
session_description = "Enter session description here."

subject_info = dict(
    subject_id="Enter optional subject id here",
    description="Enter optional subject description here",
    weight="Enter subject weight here",
    age=duration_isoformat(timedelta(days=0)),  # Enter the age of the subject in days
    species="Mus musculus",
    genotype="Enter subject genotype here",
    sex="Enter subject sex here"
)

# Set some global conversion options here
stub_test = True
use_tsync_timestamps = True
overwrite = True  # If the NWBFile exists at the path, replace it


# Automatically performs conversion based on above filepaths and options
source_data = dict(
    SyntalosEvent=dict(file_path=str(event_file_path.absolute())),
    SyntalosImage=dict(folder_path=str(video_folder_path.absolute())),
    SyntalosRecording=dict(folder_path=str(intan_folder_path.absolute()))
)
conversion_options = dict(
    SyntalosRecording=dict(stub_test=stub_test, use_timestamps=use_tsync_timestamps)
)
converter = SyntalosNWBConverter(source_data)
metadata = converter.get_metadata()
metadata['NWBFile'].update(session_description=session_description)
metadata['Subject'].update(subject_info)
converter.run_conversion(
    nwbfile_path=str(nwbfile_path.absolute()),
    metadata=metadata,
    conversion_options=conversion_options,
    overwrite=overwrite
)
