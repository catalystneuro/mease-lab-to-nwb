"""Authors: Cody Baker and Ben Dichter."""
import numpy as np

from pynwb import NWBFile, TimeSeries
from nwb_conversion_tools import IntanRecordingInterface
from hdmf.data_utils import DataChunkIterator
from hdmf.backends.hdf5.h5_utils import H5DataIO


def all_equal(lst: list):
    """Determine if all elements of a list are equal."""
    return len(set(lst)) == 1


def get_block_info(shape, size):
    """Calculate block information in binary file."""
    assert len(shape) == 2, "The shape of the blocks in the binary file must have two dimensions!"
    block_size = shape[1]
    block_stop = size // block_size + 1
    sl0 = block_size
    sl1 = sl0 + size
    return block_stop, sl0, sl1


class SyntalosRecordingInterface(IntanRecordingInterface):
    """Conversion class for Syntalos Recording + Accelerometer."""

    def run_conversion(self, nwbfile: NWBFile, metadata: dict, add_accelerometer: bool = True):
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
        super().convert_data(nwbfile=nwbfile, metadata=metadata)
        if add_accelerometer:
            accel_channels = np.array([ch for ch in self.recording_extractor._recording._anas_chan
                                       if 'AUX' in ch['name']])
            channel_conversion = [x['gain'] for x in accel_channels]
            if all_equal(channel_conversion):
                channel_conversion = np.ones(len(accel_channels))
                conversion = channel_conversion[0]
            accel_channel_units = [x['units'] for x in accel_channels]
            accel_channel_sampling_rate = [x['sampling_rate'] for x in accel_channels]

            if not all([x['offset'] == 0 for x in accel_channels]):
                raise NotImplementedError("Unable to support non-zero offsets for auxiliary channel data.")
            if not all_equal(accel_channel_units):
                raise NotImplementedError("Unequal auxiliary channel unit types are not yet supported.")
            if not all_equal(accel_channel_sampling_rate):
                raise NotImplementedError("Unequal auxiliary channel sampling rates are not yet supported.")

            def data_generator(recording, accel_channels, channels_ids):
                block_stop, sl0, sl1 = get_block_info(
                    shape=recording._recording._raw_data[accel_channels[0]['name']].shape,
                    size=recording._recording._raw_data[accel_channels[0]['name']].size
                )
                for id in channels_ids:
                    blocked_data = recording._recording._raw_data[accel_channels[id]['name']]
                    data = blocked_data[0:block_stop].flatten()[sl0:sl1]
                    yield data
            accel_data = H5DataIO(
                DataChunkIterator(
                    data=data_generator(
                        recording=self.recording_extractor,
                        accel_channels=accel_channels,
                        channels_ids=list(range(len(accel_channels)))
                    ),
                    iter_axis=1,
                    # TODO: add maxshape with proper values
                    # maxshape=(self.recording_extractor.get_num_frames(), recording.get_num_channels())
                ),
                compression='gzip'
            )
            nwbfile.add_acquisition(
                TimeSeries(
                    name="Accelerometer",
                    description="Data recorded from auxiliary channels from an intan device, tracking acceleration.",
                    data=accel_data,
                    rate=accel_channel_sampling_rate[0],
                    unit=accel_channel_units[0],
                    resolution=np.nan,
                    #channel_conversion=channel_conversion,  # not supported for TimeSeries?
                    conversion=conversion
                )
            )
            # TODO: investigate if this can all be memmaped in conjunction with DataChunkIterator
