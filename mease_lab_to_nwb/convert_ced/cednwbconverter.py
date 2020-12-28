"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
from datetime import datetime
from typing import Optional

from nwb_conversion_tools import NWBConverter, CEDRecordingInterface

from .cedstimulusinterface import CEDStimulusInterface

class CEDNWBConverter(NWBConverter):
    data_interface_classes = dict(
        CEDRecording=CEDRecordingInterface,
        CEDStimulus=CEDStimulusInterface
    )

    def __init__(self, source_data):
        channel_info = CEDRecordingInterface.get_all_channels_info(source_data['CEDRecording']['file_path'])
        rhd_channels = []
        stim_channels = []
        for ch, info in channel_info.items():
            if "Rhd" in info['title']:
                rhd_channels.append(ch)
            if info['title'] in ["CED_Mech", "MechTTL", "Laser"]:
                stim_channels.append(ch)
        source_data['CEDRecording'].update(smrx_channel_ids=rhd_channels)
        source_data['CEDStimulus'].update(smrx_channel_ids=stim_channels)
        super().__init__(source_data)

    def get_metadata(self):
        metadata = super().get_metadata()
        smrx_file_path = Path(self.data_interface_objects['CEDRecording'].source_data['file_path'])
        session_id = smrx_file_path.stem
        metadata['NWBFile'].update(
            institution="EMBL - Heidelberg",
            lab="Mease",
            session_id=session_id
        )
        return metadata
