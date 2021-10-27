"""Authors: Cody Baker and Alessio Buccino."""
import numpy as np

from pynwb import NWBFile, TimeSeries
from pynwb.misc import IntervalSeries
from pynwb.ogen import OptogeneticSeries, OptogeneticStimulusSite
from pynwb.device import Device
from hdmf.backends.hdf5.h5_utils import H5DataIO
from nwb_conversion_tools.datainterfaces.ecephys.baserecordingextractorinterface import BaseRecordingExtractorInterface
from nwb_conversion_tools.utils.json_schema import get_schema_from_method_signature
from spikeextractors import RecordingExtractor, CEDRecordingExtractor


def check_module(nwbfile, name, description=None):
    """Check if processing module exists. If not, create it. Then return module.

    Parameters
    ----------
    nwbfile: pynwb.NWBFile
    name: str
    description: str | None (optional)

    Returns
    -------
    pynwb.module
    """
    if name in nwbfile.modules:
        return nwbfile.modules[name]
    else:
        if description is None:
            description = name
        return nwbfile.create_processing_module(name, description)


def intervals_from_traces(recording: RecordingExtractor, channel_id):
    """Extract interval times from TTL pulses."""
    tr = recording.get_traces(channel_id)[0]
    dt = 1.0 / recording.get_sampling_frequency()

    timestamps = []
    data = []
    min_value = np.amin(tr)
    max_value = np.amax(tr)
    threshold = min_value + 0.5 * (max_value - min_value)
    i = 0
    n = len(tr)
    if tr[0] > threshold:
        while i < n and tr[i] > threshold:
            i = i+1
        print(f"Warning: trace starts above threshold - skipped first {i} points")
    try:
        while i < n:
            while tr[i] <= threshold:
                i = i+1
            # start
            timestamps.append(i * dt)
            data.append(+1)
            while tr[i] > threshold:
                i = i+1
            # stop
            timestamps.append(i * dt)
            data.append(-1)
    except IndexError:
        assert i == len(tr)
    if len(data) > 0 and data[-1] == 1:
        print("Warning: trace ends above threshold: ignoring last partial interval")
        timestamps.pop()
        data.pop()
    return np.array(timestamps), np.array(data, dtype="int8")


class CEDStimulusInterface(BaseRecordingExtractorInterface):
    """Primary data interface class for converting CED mechanical and cortical laser stimuli."""

    RX = CEDRecordingExtractor

    @classmethod
    def get_source_schema(cls):
        source_schema = get_schema_from_method_signature(
            class_method=cls.RX.__init__,
            exclude=['smrx_channel_ids']
        )
        source_schema.update(additionalProperties=True)
        source_schema['properties'].update(
            file_path=dict(
                type=source_schema['properties']['file_path']['type'],
                format="file",
                description="path to data file"
            )
        )
        return source_schema

    def run_conversion(self, nwbfile: NWBFile, metadata: dict = None, stub_test: bool = False):
        mech_timestamps, mech_data = intervals_from_traces(self.recording_extractor, 1)
        nwbfile.add_stimulus(
            IntervalSeries(
                name='MechanicalStimulus',
                description="Activation times inferred from TTL commands for mechanical stimulus.",
                data=mech_data,
                timestamps=mech_timestamps
            )
        )
        laser_timestamps, laser_data = intervals_from_traces(self.recording_extractor, 2)
        nwbfile.add_stimulus(
            IntervalSeries(
                name='LaserStimulus',
                description="Activation times inferred from TTL commands for cortical laser stimulus.",
                data=laser_data,
                timestamps=laser_timestamps
            )
        )
        if stub_test or self.subset_channels is not None:
            recording = self.subset_recording(stub_test=stub_test)
        else:
            recording = self.recording_extractor

        # Pressure values
        nwbfile.add_stimulus(
            TimeSeries(
                name='MechanicalPressure',
                data=H5DataIO(recording.get_traces(0).T, compression="gzip"),
                unit=self.recording_extractor._channel_smrxinfo[0]['unit'],
                conversion=recording.get_channel_property(0, 'gain'),
                rate=recording.get_sampling_frequency(),
                description="Pressure sensor attached to the mechanical stimulus used to repeatedly evoke spiking."
            )
        )

        # Laser as optogenetic stimulus
        ogen_device = nwbfile.create_device(
            name='ogen_device',
            description='ogen description'
        )
        ogen_site = OptogeneticStimulusSite(
            name="name",
            device=ogen_device,
            description='description',
            excitation_lambda=1.0,
            location='location'
        )
        nwbfile.add_ogen_site(ogen_site)
        nwbfile.add_stimulus(
            OptogeneticSeries(
                name='Laser',
                data=recording.get_traces(2)[0],
                site=ogen_site,
                rate=recording.get_sampling_frequency(),
                description="Laser TTL."
            )
        )
