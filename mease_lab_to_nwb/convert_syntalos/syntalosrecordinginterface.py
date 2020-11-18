"""Authors: Cody Baker and Ben Dichter."""
import numpy as np

from pynwb import NWBFile, TimeSeries
from nwb_conversion_tools import IntanRecordingInterface
from hdmf.backends.hdf5.h5_utils import H5DataIO


def all_equal(lst: list):
    """Determine if all elements of a list are equal."""
    return len(set(lst)) == 1


class SyntalosRecordingInterface(IntanRecordingInterface):
    """Conversion class for Syntalos Recording + Accelerometer."""

    def convert_data(self, nwbfile: NWBFile, metadata_dict: dict, add_accelerometer: bool = True):
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
        super().convert_data(nwbfile=nwbfile, metadata_dict=metadata_dict)
        if add_accelerometer:
            accel_channels = np.array([ch for ch in self.recording_extractor._recording._anas_chan
                                       if 'AUX' in ch['name']])
            channel_conversion = [x['gain'] for x in accel_channels]
            if all_equal(channel_conversion):
                channel_conversion = np.ones(len(accel_channels))
                conversion = channel_conversion[0]
            if not all_equal([[x['offset'] for x in accel_channels], 0]):
                raise NotImplementedError("Unable to support non-zero offsets for auxiliary channel data.")
            accel_channel_units = [x['units'] for x in accel_channels]
            if not all_equal(accel_channel_units):
                raise NotImplementedError("Unequal auxiliary channel unit types are not yet supported.")
            accel_channel_sampling_rate = [x['sampling_rate'] for x in accel_channels]
            if not all_equal(accel_channel_sampling_rate):
                raise NotImplementedError("Unequal auxiliary channel sampling rates are not yet supported.")
            accel_data = H5DataIO(
                self.recording_extractor._recording._read_analog(
                    channels=accel_channels,
                    dtype="uint16"
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
                    channel_conversion=channel_conversion,  # not supported for TimeSeries?
                    conversion=conversion
                )
            )
            # TODO: add DataChunkIterator? Also investigate if this can all be memmaped in conjunction with that...
