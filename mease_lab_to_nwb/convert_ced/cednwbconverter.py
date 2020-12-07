"""Authors: Cody Baker and Ben Dichter."""
from nwb_conversion_tools import NWBConverter, CEDRecordingInterface


class CEDNWBConverter(NWBConverter):
    data_interface_classes = dict(
        CEDRecording=CEDRecordingInterface,
    )

    def get_metadata(self):
        """Auto-populate as much metadata as possible."""
        metadata = super().get_metadata()
        metadata['NWBFile'].update(
            institution="EMBL - Heidelberg",
            lab="Mease"
        )
        return metadata
