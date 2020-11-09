"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
from datetime import datetime
from dateutil.parser import parse as dateparse
import toml

from nwb_conversion_tools import NWBConverter, IntanRecordingInterface


class SyntalosNWBConverter(NWBConverter):
    """Primary conversion class for Syntalos."""

    data_interface_classes = dict(
        IntanRecording=IntanRecordingInterface
    )

    def get_metadata(self):
        """Auto-populate as much metadata as possible."""
        intan_filepath = Path(self.data_interface_objects['IntanRecording'].input_args['file_path'])
        session_id = intan_filepath.stem
        subject_id = toml.load(intan_filepath.parent.parent / "attributes.toml")['subject_id']
        session_start = dateparse(
            "".join([name for name in session_id.split('_')if name.isdigit()]),
            yearfirst=True,
            dayfirst=True
        )
        metadata = super().get_metadata()
        metadata.update(
            NWBFile=dict(
                identifier=session_id,
                session_start_time=session_start.astimezone(),
                file_create_date=datetime.now().astimezone(),
                session_id=session_id,
                institution="EMBL - Heidelberg",
                lab="Mease"
            ),
            Subject=dict(
                subject_id=subject_id
            ),
            # IntanAccelerometer=dict()
        )
        return metadata
