"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
import toml
from dateparser import parse as dateparse

from nwb_conversion_tools import NWBConverter

from .syntaloseventinterface import SyntalosEventInterface
from .syntalosimageinterface import SyntalosImageInterface
from .syntalosrecordinginterface import SyntalosRecordingInterface


class SyntalosNWBConverter(NWBConverter):
    """Primary conversion class for Syntalos."""

    data_interface_classes = dict(
        SyntalosEvent=SyntalosEventInterface,
        SyntalosImage=SyntalosImageInterface,
        SyntalosRecording=SyntalosRecordingInterface
    )

    def get_metadata(self):
        intan_folder_path = Path(self.data_interface_objects['SyntalosRecording'].source_data['folder_path'])
        session_id = [x for x in intan_folder_path.iterdir() if x.suffix == ".rhd"][0].stem

        session_start = dateparse(date_string=session_id[-13:], date_formats=["%y%m%d_%H%M%S"])
        metadata = super().get_metadata()
        metadata['NWBFile'].update(
            session_start_time=session_start.astimezone(),
            session_id=session_id,
            institution="EMBL - Heidelberg",
            lab="Mease"
        )

        main_attr_file = intan_folder_path.parent / "attributes.toml"
        if main_attr_file.is_file():
            metadata.update(
                Subject=dict(
                    subject_id=toml.load(main_attr_file)['subject_id']
                )
            )

        return metadata
