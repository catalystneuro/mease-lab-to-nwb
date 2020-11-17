"""Authors: Cody Baker and Ben Dichter."""
from nwb_conversion_tools import NWBConverter, CEDRecordingInterface


class CEDNWBConverter(NWBConverter):
    data_interface_classes = dict(
        CEDRecording=CEDRecordingInterface,
    )
