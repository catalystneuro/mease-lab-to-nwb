"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
from dateparser import parse as dateparse
import toml


from .syntaloseventinterface import SyntalosEventInterface
from .syntalosimageinterface import SyntalosImageInterface

from nwb_conversion_tools import NWBConverter, IntanRecordingInterface


class SyntalosNWBConverter(NWBConverter):
    """Primary conversion class for Syntalos."""

    data_interface_classes = dict(
        SyntalosEvent=SyntalosEventInterface,
        SyntalosImage=SyntalosImageInterface,
        IntanRecording=IntanRecordingInterface
    )

    def get_metadata(self):
        """Auto-populate as much metadata as possible."""
        intan_file_path = Path(self.data_interface_objects['IntanRecording'].input_args['file_path'])
        session_id = intan_file_path.stem
        subject_id = toml.load(intan_file_path.parent.parent / "attributes.toml")['subject_id']

        session_start = dateparse(date_string=session_id[-13:], date_formats=["%y%m%d_%H%M%S"])
        metadata = super().get_metadata()
        metadata.update(
            NWBFile=dict(
                identifier=session_id,
                session_start_time=session_start.astimezone(),
                session_id=session_id,
                institution="EMBL - Heidelberg",
                lab="Mease"
            ),
            Subject=dict(
                subject_id=subject_id
            )
        )
        return metadata
