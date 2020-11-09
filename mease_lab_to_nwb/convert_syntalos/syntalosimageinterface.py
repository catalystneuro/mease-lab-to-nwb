"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
import pandas as pd
from pathlib import Path
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile
from pynwb.image import ImageSeries
from hdmf.backends.hdf5.h5_utils import H5DataIO


class SyntalosImageInterface(BaseDataInterface):
    """Conversion class for Syntalos Images."""

    @classmethod
    def get_input_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        return dict(
            required=['folder_path'],
            properties=dict(
                folder_path=dict(type='string')
            )
        )

    def convert_data(self, nwbfile: NWBFile, metadata_dict: dict, stub_test: bool = False):
        """
        Primary conversion function for the custom Syntalos image interface.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata_dict : dict
        stub_test : bool, optional
            If true, truncates all data to a small size for fast testing. The default is False.
        """
        video_folder = Path(self.input_args['folder_path'])
        video_file_path_list = [str(x.absolute()) for x in video_folder.iterdir() if x.suffix == ".mkv"]

        video_timestamps = list()
        for video_file_path in video_file_path_list:
            video_time_file = pd.read_csv(video_file_path.replace(".mkv", "_timestamps.csv"), header=0)
            video_timestamps.append(np.array([int(x.split(";")[1]) for x in video_time_file['frame; timestamp']]))

        # Custom labeled events
        videos = ImageSeries(
            name='Videos',
            description="Videos recorded by TIS camera.",
            format="external",
            external_file=video_file_path_list,
            timestamps=video_timestamps[0],
        )
        nwbfile.add_acquisition(videos)
