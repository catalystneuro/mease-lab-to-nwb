"""Authors: Alessio Buccino and Cody Baker."""
from spikeextractors import IntanRecordingExtractor, MultiRecordingTimeExtractor
from pathlib import Path
from datetime import datetime
import numpy as np
from edlio.dataio.tsyncfile import TSyncFile, LegacyTSyncFile


# class SyntalosRecordingExtractor(folder_path):
#     """
#     Routes the correct parameters to a SyntalosSingleRecordingExtractor or a SyntalosMultiRecordingExtractor.

#     Parameters
#     ----------
#     folder_path: str or Path
#         The Syntalos root folder

#     Returns
#     -------
#     recording: SyntalosSingleRecordingExtractor or SyntalosMultiRecordingExtractor
#         The recording extractor (depending on the number of .rhd files in the Syntalos folder)
#     """
#     folder_path = Path(folder_path)

#     assert folder_path.is_dir(), "The provided Syntalos folder does not exists"
#     intan_signal = folder_path / "intan-signals"
#     assert intan_signal.is_dir(), "The intan-signals is not found in the Syntalos folder"
#     rhd_files = [p for p in intan_signal.iterdir() if p.suffix == ".rhd"]

#     assert len(rhd_files) > 0, "No rhd files found in the Syntalos folder"

#     if len(rhd_files) == 1:
#         return SyntalosSingleRecordingExtractor(rhd_files[0])
#     else:
#         return SyntalosMultiRecordingExtractor(rhd_files)


# class SyntalosSingleRecordingExtractor(IntanRecordingExtractor):
#     """
#     Class to extract Syntalos datasets with a single .rhd file.

#     The recording extractor is an IntanRecordingExtractor, but synchronization is performed using the .tsync file

#     Parameters
#     ----------
#     file_path: str or Path
#         The path to the .rhd file
#     """

#     def __init__(self, file_path):
#         file_path = Path(file_path)
#         assert file_path.is_file(), "The provided file does not exist!"
#         assert file_path.suffix == ".rhd", "The provided file is not an '.rhd' file!"
#         tsync_files = [p for p in file_path.parent.iterdir() if p.suffix == ".tsync"]
#         assert len(tsync_files) == 1, "Only one tsync file should be present in the Syntalos folder!"

#         super().__init__(file_path)
#         self._timestamps = _get_timestamps_with_tsync(self, tsync_files[0])

#         self._kwargs = dict(file_path=str(file_path.absolute()))

#     def frame_to_time(self, frame):
#         return self._timestamps[frame]

#     def time_to_frame(self, time):
#         return np.searchsorted(self._timestamps, time).astype('int64')


# class SyntalosMultiRecordingExtractor(MultiRecordingTimeExtractor):
class SyntalosRecordingExtractor(MultiRecordingTimeExtractor):
    """
    Class to extract Syntalos datasets with a multiple .rhd files.

    The recording extractor is an MultiRecordingTimeExtractor with multiple IntanRecordingExtractors,
    but synchronization is performed using the .tsync file.

    Parameters
    ----------
    folder_path: str or Path
        The path to the .rhd files
    """

    def __init__(self, folder_path: str):
        file_paths = [p for p in Path(folder_path).iterdir() if p.suffix == ".rhd"]
        for file_path in file_paths:
            assert file_path.is_file(), "The provided file does not exist!"
            assert file_path.suffix == '.rhd', "The provided file is not an '.rhd' file!"
        assert len(file_paths) >= 1, "No rhd files found in the folder path!"
        tsync_files = [p for p in file_paths[0].parent.iterdir() if p.suffix == '.tsync']
        assert len(tsync_files) == 1, "Only one tsync file should be present in the Syntalos folder!"

        # order rhd files by date
        dates = []
        for file_path in file_paths:
            file_name = file_path.stem
            date = datetime.strptime("-".join(file_name.split("_")[-2:]), "%y%m%d-%H%M%S")
            dates.append(date)
        files_sorted = np.array(file_paths)[np.argsort(dates)]

        recordings = []
        for file_path in files_sorted:
            intan_recording = IntanRecordingExtractor(file_path=file_path, dtype="uint16")
            recordings.append(intan_recording)

        super().__init__(recordings)
        self._timestamps = _get_timestamps_with_tsync(self, tsync_files[0])

        self._kwargs = dict(file_paths=[str(file_path.absolute()) for file_path in file_paths])

    def frame_to_time(self, frame):
        return self._timestamps[frame]

    def time_to_frame(self, time):
        return np.searchsorted(self._timestamps, time).astype('int64')


def _get_timestamps_with_tsync(recording, tsync_file):
    try:
        tsync = TSyncFile(tsync_file)
    except:
        try:
            tsync = LegacyTSyncFile(tsync_file)
        except:
            raise RuntimeError("The .tsync file could not be parsed.")

    sync_map = tsync.times
    num_frames = recording.get_num_frames()
    sampling_frequency = recording.get_sampling_frequency()
    tv_usec = np.arange(num_frames, dtype=np.float64) / sampling_frequency * 1E6
    tv_adj_usec = np.arange(num_frames, dtype=np.float64) / sampling_frequency * 1E6

    init_offset_usec = offset_usec = sync_map[0][0] - sync_map[0][1]
    idx = np.where(tv_usec <= sync_map[0][0])[0]
    tv_adj_usec[idx] -= init_offset_usec

    for s, sync in enumerate(sync_map):
        if s < len(sync_map) - 1:
            idx = np.where((tv_usec > sync[0]) & (tv_usec <= sync_map[s + 1][0]))[0]
            offset_usec = sync_map[s + 1][0] - sync_map[s + 1][1]
        else:
            idx = np.where(tv_usec > sync[0])[0]
        tv_adj_usec[idx] -= offset_usec

    return tv_adj_usec / 1E6
