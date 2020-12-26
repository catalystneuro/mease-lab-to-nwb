"""Authors: Cody Baker."""
from pynwb import NWBFile, TimeSeries
from hdmf.backends.hdf5.h5_utils import H5DataIO
from nwb_conversion_tools import CEDRecordingInterface


class CEDMechStimulusInterface(CEDRecordingInterface):
    """Primary data interface class for converting CED mechanical stimuli."""

    def run_conversion(self, nwbfile: NWBFile, metadata: dict = None, stub_test: bool = False):
        if stub_test or self.subset_channels is not None:
            recording = self.subset_recording(stub_test=stub_test)
        else:
            recording = self.recording_extractor

        nwbfile.add_stimulus(
            TimeSeries(
                name='MechStimulus',
                data=H5DataIO(recording.get_traces(), compression="gzip"),
                unit=self.recording_extractor._channel_smrxinfo[0]['unit'],
                conversion=recording.get_channel_property(0, 'gain'),
                rate=recording.get_sampling_frequency(),
                description="TTL command for mechanical stimulus."
            )
        )
