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
                data_len = self.get_num_frames()
                sample_rate = self.get_sampling_frequency()
                sync_map = tsync.times
                data_pos_idx = 0
                sync_idx = 0
                offset_usec = sync_map[0, 0] - sync_map[0, 1]

                tvec, offset_usec, sync_idx = make_synced_tsvec(data_len,
                                                                sample_rate,
                                                                sync_map,
                                                                data_pos_idx,
                                                                sync_idx,
                                                                offset_usec)

                self._times = np.squeeze(tvec) / 1000

        self._recording = se.IntanRecordingExtractor

        self._kwargs = {'folder_path': str(file_or_folder_path.absolute())}

    def frame_to_time(self, frame):
        return self._times[frame]

    # TODO use bisect
    def time_to_frame(self, time):
        tdiffs = self._times - time
        return np.argmin(tdiffs).astype('int64')


### Helper functions from edlio.dataio.rhd.read_rhc
def first_ge_index(vec, c):
    ''' Get the index of the first greater-equal number to `c`
    in ascending-sorted vector `vec` '''
    for i in range(len(vec)):
        if vec[i] >= c:
            return i
    return np.nan


def make_synced_tsvec(data_len, sample_rate, sync_map, index_offset, init_sync_idx, init_offset_usec):
    ''' Create time vector, synchronizing all timepoints. '''
    offset_usec = init_offset_usec
    sync_idx = init_sync_idx

    tv_adj = np.zeros((data_len, 1), dtype=np.float64)
    for i in range(data_len):
        ts_msec = ((i + index_offset) / sample_rate) * 1000
        ts_usec = ts_msec * 1000

        ns_idx = first_ge_index(sync_map[:, 0][sync_idx:], ts_usec) + sync_idx
        if ns_idx > sync_idx:
            sync_idx = ns_idx
            offset_usec = sync_map[sync_idx][0] - sync_map[sync_idx][1]

        tv_adj[i] = ts_msec - (offset_usec / 1000)

    return tv_adj, offset_usec, sync_idx