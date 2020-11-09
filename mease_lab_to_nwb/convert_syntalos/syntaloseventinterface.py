"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
import pandas as pd
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile
from ndx_events import LabeledEvents, AnnotatedEventsTable


class SyntalosEventInterface(BaseDataInterface):
    """Description here."""

    @classmethod
    def get_input_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        return dict(
            required=['folder_path'],
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

        # Custom labeled events
        events = LabeledEvents(
            name='LabeledEvents',
            description='Events from the experiment.',
            timestamps=event_timestamps,
            resolution=np.nan,
            data=event_data,
            labels=event_labels
        )
        nwbfile.add_acquisition(events)

        # Reward events
        # create a new AnnotatedEventsTable type to hold annotated events
        # annotated_events = AnnotatedEventsTable(
        #     name='EventTable',
        #     description='annotated events from my experiment',
        #     resolution=1e-5  # resolution of the timestamps, i.e., smallest possible difference between timestamps
        # )
        # # add a custom indexed (ragged) column to represent whether each event time was a bad event
        # annotated_events.add_column(
        #     name='bad_event',
        #     description='whether each event time should be excluded',
        #     index=True
        # )
        # # add an event type (row) to the AnnotatedEventsTable instance
        # annotated_events.add_event_type(
        #     label='Reward',
        #     event_description='Times when the subject received reward.',
        #     event_times=[1., 2., 3.],
        #     bad_event=[False, False, True],
        #     id=3
        # )

        # # create a processing module in the NWB file to hold processed events data
        # events_module = nwbfile.create_processing_module(
        #     name='events',
        #     description='processed event data'
        # )
        
        # # add the AnnotatedEventsTable instance to the processing module
        # events_module.add(annotated_events)
