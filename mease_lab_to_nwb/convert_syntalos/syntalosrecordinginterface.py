"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from tempfile import TemporaryFile
from pathlib import Path

from pynwb import NWBFile, TimeSeries
from nwb_conversion_tools.baserecordingextractorinterface import BaseRecordingExtractorInterface
from nwb_conversion_tools import IntanRecordingInterface
from hdmf.data_utils import DataChunkIterator
from hdmf.backends.hdf5.h5_utils import H5DataIO

from .syntalosrecordingextractor import SyntalosRecordingExtractor


def all_equal(lst: list):
    """Determine if all elements of a list are equal."""
    return len(set(lst)) == 1


# TODO: allow buffer_mb to be specified top-down (currently defaulting)
def write_accelerometer_data(nwbfile: NWBFile, recording, stub_test: bool = False, buffer_mb: int = 500,
                             use_timestamps: bool = False):
    """
    Add accelerometer data from a single rhd file to the NWBFile.

    Expects full timestamps from the higher-frequency recording extractor.
    """
    accel_channels = np.array([ch for ch in recording._recordings[0]._recording._anas_chan if 'AUX' in ch['name']])
    channel_conversion = [x['gain'] for x in accel_channels]
    accel_channel_units = [x['units'] for x in accel_channels]
    accel_channel_sampling_rate = [x['sampling_rate'] for x in accel_channels]

    if not all_equal(channel_conversion):
        raise NotImplementedError("Writing TimeSeries in NWBFiles with channel conversion factors is not supported!")
    if not all([x['offset'] == 0 for x in accel_channels]):
        raise NotImplementedError("Unable to support non-zero offsets for auxiliary channel data.")
    if not all_equal(accel_channel_units):
        raise NotImplementedError("Unequal auxiliary channel unit types are not yet supported.")
    if not all_equal(accel_channel_sampling_rate):
        raise NotImplementedError("Unequal auxiliary channel sampling rates are not yet supported.")
    if not isinstance(recording._recordings[0]._recording._raw_data[accel_channels[0]['name']], np.memmap):
        raise NotImplementedError("Writing accelerometer data for non-memory maps is not supported!")

    conversion = channel_conversion[0]
    accel_sampling_rate = accel_channel_sampling_rate[0]
    all_memmaps = [
        [x._recording._raw_data[accel_channels[j]['name']].flatten() for j in range(accel_channels.size)]
        for x in recording._recordings
    ]
    lens = [x[0].size for x in all_memmaps]
    total_length = sum(lens)
    all_accel_data = np.memmap(
        filename=TemporaryFile(),
        dtype=recording.get_dtype(),
        mode="w+",
        shape=(total_length, accel_channels.size)
    )
    cumlens = np.insert(np.cumsum(lens), 0, 0)
    for j, x in enumerate(all_memmaps):
        for n, y in enumerate(x):
            all_accel_data[cumlens[j]:cumlens[j+1], n] = y
    n_bytes = np.dtype(recording.get_dtype()).itemsize
    buffer_size = int(buffer_mb * 1e6) // (accel_channels.size * n_bytes)

    if stub_test:
        all_accel_data = all_accel_data[0:100, :]

    accel_data = DataChunkIterator(
        data=all_accel_data,
        buffer_size=buffer_size
    )
    tseries_kwargs = dict(
        name="Accelerometer",
        description="Data recorded from auxiliary channels from an intan device, tracking acceleration.",
        data=H5DataIO(accel_data, compression="gzip"),
        unit=accel_channel_units[0],
        resolution=np.nan,
        conversion=conversion
    )

    if not use_timestamps:
        tseries_kwargs.update(rate=accel_sampling_rate)
    else:
        accel_timestamps = recording.frame_to_time(
            recording.time_to_frame(np.arange(0, all_accel_data.shape[0]) / accel_sampling_rate)
        )
        tseries_kwargs.update(timestamps=H5DataIO(accel_timestamps, compression="gzip"))

    nwbfile.add_acquisition(TimeSeries(**tseries_kwargs))


class SyntalosRecordingInterface(BaseRecordingExtractorInterface):
    """Conversion class for Syntalos Recording + Accelerometer."""

    RX = SyntalosRecordingExtractor

    def get_metadata(self):
        intan_filepath = [x for x in Path(self.source_data['folder_path']).iterdir() if x.suffix == ".rhd"][0]
        temp_intan_interface = IntanRecordingInterface(file_path=intan_filepath)
        return temp_intan_interface.get_metadata()

    def run_conversion(self, nwbfile: NWBFile, metadata: dict, stub_test: bool = False, add_accelerometer: bool = True,
                       use_timestamps: bool = False):
        """
        Primary conversion function for Syntalos recordings.

        Parameters
        ----------
        nwbfile : NWBFile
        metadata_dict : dict
        stub_test : bool, optional
            If true, truncates all data to a small size for fast testing. The default is False.
        add_accelerometer: bool, optional
            If true, adds the separate recording channels for accelerometer information. The default is True.
        """
        super().run_conversion(nwbfile=nwbfile, metadata=metadata, stub_test=stub_test, use_timestamps=use_timestamps)
        if add_accelerometer:
            write_accelerometer_data(
                nwbfile=nwbfile,
                recording=self.recording_extractor,
                stub_test=stub_test,
                use_timestamps=use_timestamps
            )
