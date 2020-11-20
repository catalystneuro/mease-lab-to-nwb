import spikeextractors as se
from spikeextractors.extraction_tools import check_get_traces_args, check_get_ttl_args
from pathlib import Path
from datetime import datetime
import numpy as np
from edlio.dataio.tsyncfile import TSyncFile, LegacyTSyncFile


# TODO ideally deal with multiple RHD files
class SyntalosRecordingExtractor(se.IntanRecordingExtractor):
    def __init__(self, file_or_folder_path):
        file_or_folder_path = Path(file_or_folder_path)
        if file_or_folder_path.is_dir():
            folder_path = file_or_folder_path
            intan_signal = folder_path / 'intan-signals'
            rhd_files = [p for p in intan_signal.iterdir() if p.suffix == '.rhd']
            assert len(rhd_files) == 1, "Multiple rhd files found. Pleas pass the path to the .rhd file to be loaded."
            rhd_file = rhd_files[0]
            tsync_files = [p for p in intan_signal.iterdir() if p.suffix == '.tsync']
        elif file_or_folder_path.is_dir():
            assert file_or_folder_path.suffix == '.rhd'
            tsync_files = [p for p in file_or_folder_path.parent.iterdir() if p.suffix == '.tsync']
            rhd_file = file_or_folder_path
        else:
            raise AttributeError(f"{file_or_folder_path.name} is not a Syntalos folder or an rhd file")

        super().__init__(rhd_file)
        self._times = None

        if len(tsync_files) == 0:
            self._sync = False
        elif len(tsync_files) > 1:
            # TODO find file with same stem
            raise NotImplementedError
        else:
            self._sync = True
            try:
                tsync = TSyncFile(tsync_files[0])
            except:
                try:
                    tsync = LegacyTSyncFile(tsync_files[0])
                except:
                    self._sync = False
            if self._sync:
                self.sync_map = tsync.times
                self.sync_times()

        self._kwargs = {'folder_path': str(file_or_folder_path.absolute())}

    def frame_to_time(self, frame):
        return self._times[frame]

    def time_to_frame(self, time):
        return np.searchsorted(self._times, time).astype('int64')

    def sync_times(self):
        tv_usec = np.arange(self.get_num_frames(), dtype=np.float64) / self.get_sampling_frequency() * 1E6
        tv_adj_usec = np.arange(self.get_num_frames(), dtype=np.float64) / self.get_sampling_frequency() * 1E6

        init_offset_usec = offset_usec = self.sync_map[0][0] - self.sync_map[0][1]
        idx = np.where(tv_usec <= self.sync_map[0][0])[0]
        tv_adj_usec[idx] -= init_offset_usec

        for s, sync in enumerate(self.sync_map):
            if s < len(self.sync_map) - 1:
                idx = np.where((tv_usec > sync[0]) & (tv_usec <= self.sync_map[s + 1][0]))[0]
                offset_usec = self.sync_map[s + 1][0] - self.sync_map[s + 1][1]
            else:
                idx = np.where(tv_usec > sync[0])[0]
            tv_adj_usec[idx] -= offset_usec

        self._times = tv_adj_usec / 1E6
