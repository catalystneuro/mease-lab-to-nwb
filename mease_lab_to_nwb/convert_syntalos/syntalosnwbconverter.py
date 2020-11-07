"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
from datetime import datetime
from dateutil.parser import parse as dateparse

from nwb_conversion_tools import NWBConverter, IntanRecordingInterface


class SyntalosNWBConverter(NWBConverter):
    """Primary conversion class for Syntalos."""

    data_interface_classes = dict(
        IntanRecording=IntanRecordingInterface,
    )

    def get_metadata(self):
        """Auto-populate as much metadata as possible."""
        session_id = Path(self.data_interface_objects['IntanRecording'].input_args['file_path']).stem
        session_start = dateparse(
            "".join([name for name in session_id.split('_')if name.isdigit()]),
            yearfirst=True,
            dayfirst=True
        )
        metadata = dict(
            NWBFile=dict(
                identifier=session_id,
                session_start_time=session_start.astimezone(),
                file_create_date=datetime.now().astimezone(),
                session_id=session_id,
                institution="EMBL - Heidelberg",
                lab="Mease"
            ),
            Subject=dict(),
            IntanRecording=None,
            # IntanAccelerometer=dict()
        )
        return metadata
