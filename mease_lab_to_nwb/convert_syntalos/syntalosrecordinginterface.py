"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from pathlib import Path

from spikeextractors import NwbRecordingExtractor
from pynwb import NWBFile, TimeSeries
from nwb_conversion_tools.baserecordingextractorinterface import BaseRecordingExtractorInterface
from nwb_conversion_tools import IntanRecordingInterface
from hdmf.backends.hdf5.h5_utils import H5DataIO

from .syntalosrecordingextractor import SyntalosRecordingExtractor


def all_equal(lst: list):
    """Determine if all elements of a list are equal."""
    return len(set(lst)) == 1


def write_accelerometer_data(nwbfile: NWBFile, recording, stub_test: bool = False, use_timestamps: bool = False):
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

    all_accel_data = np.concatenate(np.moveaxis(np.array(all_memmaps), 2, 1))
    if stub_test:
        all_accel_data = all_accel_data[:100, :]

    tseries_kwargs = dict(
        name="Accelerometer",
        description="Data recorded from auxiliary channels from an intan device, tracking acceleration.",
        data=H5DataIO(all_accel_data, compression="gzip"),
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
        recording_extractor = self.subset_recording(stub_test=stub_test)
        NwbRecordingExtractor.write_recording(
            recording_extractor,
            nwbfile=nwbfile,
            metadata=metadata,
            use_timestamps=use_timestamps
        )
        if add_accelerometer:
            write_accelerometer_data(
                nwbfile=nwbfile,
                recording=self.recording_extractor,
                stub_test=stub_test,
                use_timestamps=use_timestamps
            )
