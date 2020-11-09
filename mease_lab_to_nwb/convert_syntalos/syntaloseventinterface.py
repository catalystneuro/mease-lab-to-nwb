"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
import pandas as pd
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile
from ndx_events import LabeledEvents, AnnotatedEventsTable
from hdmf.backends.hdf5.h5_utils import H5DataIO


class SyntalosEventInterface(BaseDataInterface):
    """Conversion class for Syntalos Events."""

    @classmethod
    def get_input_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        return dict(
            required=['file_path'],
            properties=dict(
                file_path=dict(type='string')
            )
        )

    def convert_data(self, nwbfile: NWBFile, metadata_dict: dict, stub_test: bool = False):
        """
        Primary conversion function for the custom Syntalos event interface.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata_dict : dict
        stub_test : bool, optional
            If true, truncates all data to a small size for fast testing. The default is False.
        """
        event_file = self.input_args['file_path']
        events_data = pd.read_csv(event_file, header=0)
        split_first_col = [x.split(";") for x in events_data['Time;Tag;Description']]
        event_timestamps = [int(x[0]) for x in split_first_col]
        event_labels = [x[1] for x in split_first_col]
        unique_events = set(event_labels)
        events_map = {event: n for n, event in enumerate(unique_events)}
        event_data = [events_map[event] for event in event_labels]
        reward_events = [pd.isna(x) for x in events_data['Unnamed: 1']]

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

        # Reward events
        # annotated_events = AnnotatedEventsTable(
        #     name='EventTable',
        #     description='Events from the experiment.',
        #     resolution=np.nan
        # )
        # annotated_events.add_column(
        #     name='reward',
        #     description='whether each event time should be excluded',
        #     index=True
        # )
        # annotated_events.add_event_type(
        #     label='Reward',
        #     event_description='Times when the subject received reward.',
        #     event_times=event_timestamps,  # does not support compression
        #     reward=H5DataIO(reward_events, compression="gzip")
        # )
        # events_module = nwbfile.create_processing_module(
        #     name='Events',
        #     description='Processed event data.'
        # )
        # events_module.add(annotated_events)
