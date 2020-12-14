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
        return dict(
            required=['file_path'],
            properties=dict(
                file_path=dict(type='string')
            )
        )

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        event_file = self.source_data['file_path']
        events_data = pd.read_csv(event_file, delimiter=";")
        event_timestamps = events_data['Time'].to_numpy() / 1E3
        event_labels = events_data['Tag'].to_numpy()
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
