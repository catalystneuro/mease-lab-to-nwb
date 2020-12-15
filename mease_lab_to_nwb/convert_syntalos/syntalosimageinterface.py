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
        return dict(
            required=['folder_path'],
            properties=dict(
                folder_path=dict(type='string')
            )
        )

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        video_folder = Path(self.source_data['folder_path'])
        video_file_path_list = [str(x) for x in video_folder.iterdir() if x.suffix == ".mkv"]

        video_timestamps = np.empty(0)
        for video_file_path in video_file_path_list:
            video_time_df = pd.read_csv(
                video_file_path.replace(".mkv", "_timestamps.csv"),
                delimiter=";",
                skipinitialspace=True
            )
            video_timestamps = np.append(video_timestamps, video_time_df['timestamp'].to_numpy() / 1E3)

        # Custom labeled events
        videos = ImageSeries(
            name='Videos',
            description="Videos recorded by TIS camera.",
            format="external",
            external_file=video_file_path_list,
            timestamps=H5DataIO(video_timestamps, compression="gzip")
        )
        nwbfile.add_acquisition(videos)
