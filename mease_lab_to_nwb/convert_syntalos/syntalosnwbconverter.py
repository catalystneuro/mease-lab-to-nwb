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

    def run_conversion(self, metadata: dict, nwbfile_path: str = None, save_to_file: bool = True,
                       conversion_options: dict = None):
        for interface_name in ['SyntalosImage', 'SyntalosEvent']:
            if interface_name in self.data_interface_objects \
                    and conversion_options[interface_name].get('use_timestamps', False):
                assert 'SyntalosRecording' in self.data_interface_objects, \
                    f"Requesting to use tsync timestamps in {interface_name}Interface, but no recording is present!"
                conversion_options[interface_name].update(
                    timestamps=list(self.data_interface_objects['SyntalosRecording'].recording_extractor.get_timestamps())
                )
        super().run_conversion(
            metadata=metadata,
            nwbfile_path=nwbfile_path,
            save_to_file=save_to_file,
            conversion_options=conversion_options
        )
