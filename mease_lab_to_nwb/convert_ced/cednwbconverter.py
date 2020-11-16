"""Authors: Cody Baker and Ben Dichter."""
import os
from datetime import datetime, timedelta

from dateutil.parser import parse as dateparse
from isodate import duration_isoformat
from nwb_conversion_tools import NWBConverter, CEDRecordingInterface

from ..utils import convert_mat_file_to_dict


class CEDNWBConverter(NWBConverter):
    data_interface_classes = dict(
        CEDRecording=CEDRecordingInterface,
    )
