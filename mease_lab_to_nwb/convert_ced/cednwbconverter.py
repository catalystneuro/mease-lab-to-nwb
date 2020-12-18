"""Authors: Cody Baker and Ben Dichter."""
from nwb_conversion_tools import NWBConverter, CEDRecordingInterface


class CEDNWBConverter(NWBConverter):
    data_interface_classes = dict(
        CEDRecording=CEDRecordingInterface,
    )

    def __init__(self, source_data):
        channel_info = CEDRecordingInterface.get_all_channels_info(source_data['CEDRecording']['file_path'])
        rhd_channels = []
        for ch, info in channel_info.items():
            if "Rhd" in info["title"]:
                rhd_channels.append(ch)
        source_data['CEDRecording'].update(smrx_channel_ids=rhd_channels)
        super().__init__(source_data)

    def get_metadata(self):
        """Auto-populate as much metadata as possible."""
        metadata = super().get_metadata()
        metadata['NWBFile'].update(
            institution="EMBL - Heidelberg",
            lab="Mease"
        )
        return metadata
