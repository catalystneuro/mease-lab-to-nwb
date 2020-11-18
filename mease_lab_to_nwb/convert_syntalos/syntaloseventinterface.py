"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
import pandas as pd
from hdmf.backends.hdf5.h5_utils import H5DataIO
from ndx_events import LabeledEvents
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile


class SyntalosEventInterface(BaseDataInterface):
    """Conversion class for Syntalos Events."""

    @classmethod
    def get_source_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        return dict(
            required=['file_path'],
            properties=dict(
                file_path=dict(type='string')
            )
        )

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        """
        Primary conversion function for the custom Syntalos event interface.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata_dict : dict
        stub_test : bool, optional
            If true, truncates all data to a small size for fast testing. The default is False.
        """
        event_file = self.source_data['file_path']
        events_data = pd.read_csv(event_file, header=0)
        split_first_col = [x.split(";") for x in events_data['Time;Tag;Description']]
        event_timestamps = [int(x[0]) for x in split_first_col]
        event_labels = [x[1] for x in split_first_col]
        unique_events = set(event_labels)
        events_map = {event: n for n, event in enumerate(unique_events)}
        event_data = [events_map[event] for event in event_labels]

        # Custom labeled events
        events = LabeledEvents(
            name='LabeledEvents',
            description='Events from the experiment.',
            timestamps=H5DataIO(event_timestamps, compression="gzip"),
            resolution=np.nan,
            data=H5DataIO(event_data, compression="gzip"),
            labels=list(unique_events)  # does not suppoort compression
        )
        nwbfile.add_acquisition(events)
