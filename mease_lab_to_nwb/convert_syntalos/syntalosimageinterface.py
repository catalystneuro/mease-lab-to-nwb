"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
import numpy as np
import pandas as pd

from hdmf.backends.hdf5.h5_utils import H5DataIO
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile
from pynwb.image import ImageSeries


class SyntalosImageInterface(BaseDataInterface):
    """Conversion class for Syntalos Images."""

    @classmethod
    def get_source_schema(cls):
        """Return a partial JSON schema indicating the input arguments and their types."""
        return dict(
            required=['folder_path'],
            properties=dict(
                folder_path=dict(type='string')
            )
        )

    def run_conversion(self, nwbfile: NWBFile, metadata: dict, use_timestamps: bool = False,
                       timestamps: list = None):
        """
        Primary conversion function for the custom Syntalos image interface.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata_dict : dict
        stub_test : bool, optional
            If true, truncates all data to a small size for fast testing. The default is False.
        use_timestamps : bool, optional
            If true, synchronizes the reported video timestamps with the tsync file from the recording
        recording : RecordingExtractor, optional
            Only used (and required) if use_timestamps is true
        """
        video_folder = Path(self.source_data['folder_path'])
        video_file_path_list = [str(x.absolute()) for x in video_folder.iterdir() if x.suffix == ".mkv"]

        video_timestamps = np.empty(0)
        for video_file_path in video_file_path_list:
            video_time_file = pd.read_csv(video_file_path.replace(".mkv", "_timestamps.csv"), header=0)
            video_timestamps = np.append(
                video_timestamps,
                [int(x.split(";")[1]) / 1E3 for x in video_time_file['frame; timestamp']]
            )

        if use_timestamps:
            print(timestamps[0:20])
            print(video_timestamps[0:20])
            max_frame = len(timestamps)
            print(max_frame)
            print(len(video_timestamps >= max_frame))
            nearest_frames = np.searchsorted(timestamps, video_timestamps).astype('int64')
            synched_timestamps = [timestamps[x] for x in nearest_frames if x < max_frame]
            synched_timestamps.extend(list(video_timestamps[video_timestamps >= max_frame]))
            video_timestamps = synched_timestamps

        # Custom labeled events
        videos = ImageSeries(
            name='Videos',
            description="Videos recorded by TIS camera.",
            format="external",
            external_file=video_file_path_list,
            timestamps=H5DataIO(video_timestamps, compression="gzip")
        )
        nwbfile.add_acquisition(videos)
