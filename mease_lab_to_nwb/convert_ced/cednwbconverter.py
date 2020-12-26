"""Authors: Cody Baker and Ben Dichter."""
from nwb_conversion_tools import NWBConverter, CEDRecordingInterface

from .cedmechstimulusinterface import CEDMechStimulusInterface
from .cedlaserstimulusinterface import CEDLaserStimulusInterface


class CEDNWBConverter(NWBConverter):
    data_interface_classes = dict(
        CEDRecording=CEDRecordingInterface,
        CEDMechStimulus=CEDMechStimulusInterface,
        CEDLaserStimulus=CEDLaserStimulusInterface
    )

    def __init__(self, source_data):
        channel_info = CEDRecordingInterface.get_all_channels_info(source_data['CEDRecording']['file_path'])
        rhd_channels = []
        for ch, info in channel_info.items():
            if "Rhd" in info['title']:
                rhd_channels.append(ch)
            if "MechStim" in info['title']:
                mech_stim_channel = ch
            if "Laser" in info['title']:
                laster_stim_channel = ch
        source_data['CEDRecording'].update(smrx_channel_ids=rhd_channels)
        source_data['CEDMechStimulus'].update(smrx_channel_ids=[mech_stim_channel])
        source_data['CEDLaserStimulus'].update(smrx_channel_ids=[laster_stim_channel])
        super().__init__(source_data)

    def get_metadata(self):
        """Auto-populate as much metadata as possible."""
        metadata = super().get_metadata()
        metadata['NWBFile'].update(
            institution="EMBL - Heidelberg",
            lab="Mease"
        )
        return metadata
