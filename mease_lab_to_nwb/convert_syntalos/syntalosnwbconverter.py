"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path

import toml
from dateparser import parse as dateparse
from nwb_conversion_tools import NWBConverter, IntanRecordingInterface

from syntaloseventinterface import SyntalosEventInterface
from syntalosimageinterface import SyntalosImageInterface
from syntalosrecordinginterface import SyntalosRecordingInterface

class SyntalosNWBConverter(NWBConverter):
    """Primary conversion class for Syntalos."""

    data_interface_classes = dict(
        SyntalosEvent=SyntalosEventInterface,
        SyntalosImage=SyntalosImageInterface,
        SyntalosRecording=SyntalosRecordingInterface
    )

    def get_metadata(self):
        """Auto-populate as much metadata as possible."""
        intan_folder_path = Path(self.data_interface_objects['SyntalosRecording'].source_data['folder_path'])
        session_id = [x for x in intan_folder_path.iterdir() if x.suffix == ".rhd"][0].stem
        subject_id = toml.load(intan_folder_path.parent / "attributes.toml")['subject_id']

        session_start = dateparse(date_string=session_id[-13:], date_formats=["%y%m%d_%H%M%S"])
        metadata = super().get_metadata()
        metadata['NWBFile'].update(
            session_start_time=session_start.astimezone(),
            session_id=session_id,
            institution="EMBL - Heidelberg",
            lab="Mease"
        )
        metadata.update(
            Subject=dict(
                subject_id=subject_id
            )
        )
        return metadata
