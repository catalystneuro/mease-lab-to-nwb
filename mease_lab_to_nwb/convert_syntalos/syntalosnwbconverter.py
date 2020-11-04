"""Authors: Cody Baker and Ben Dichter."""
import os
from datetime import datetime, timedelta

from dateutil.parser import parse as dateparse
from isodate import duration_isoformat
# TODO: Need to add IntanRecordingInterface over on nwb-conversion-tools, or use Ben's suggested auto-class creation function
from nwb_conversion_tools import NWBConverter, IntanRecordingInterface

from ..utils import convert_mat_file_to_dict


class SyntalosNWBConverter(NWBConverter):
    data_interface_classes = dict()

    def __init__(self, **input_args):
        super().__init__(**input_args)

    def get_metadata(self):

        return dict(
            NWBFile=dict(
                #identifier="fill_me",
                #session_start_time=datetime.datetime("fill me"),
                #session_id="fill me",
                institution="Heidelberg",
                #lab="fill me"
            ),
            Subject=dict(),
        )
