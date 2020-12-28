"""Authors: Cody Baker and Alessio Buccino."""
import numpy as np

from pynwb import NWBFile, TimeSeries
from pynwb.epoch import TimeIntervals
from hdmf.backends.hdf5.h5_utils import H5DataIO
from nwb_conversion_tools.baserecordingextractorinterface import BaseRecordingExtractorInterface
from nwb_conversion_tools.json_schema_utils import get_schema_from_method_signature
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


def intervals_from_traces(recording: RecordingExtractor):
    """Extract interval times from TTL pulses."""
    traces = recording.get_traces(channel_ids=[1, 2])
    sf = recording.get_sampling_frequency()

    ttls = []
    states = []
    for tr in traces:
        threshold = np.ptp(tr) / 2 + np.min(tr)
        crossings = np.array(tr > threshold).astype("int8")

        rising = np.nonzero(np.diff(crossings, 1) > 0)[0]
        falling = np.nonzero(np.diff(crossings, 1) < 0)[0]

        ttl = np.concatenate((rising, falling))
        sort_order = np.argsort(ttl)
        ttl = np.sort(ttl)
        state = [1] * len(rising) + [-1] * len(falling)
        state = np.array(state)[sort_order]

        ttls.append(ttl)
        states.append(state)

    conditions = []
    for ttl, state in zip(ttls, states):
        assert len(ttl[state == 1]) == len(ttl[state == -1]), "Different number of rising/falling edges!"
        condition = np.zeros((len(ttl[state == 1]), 2), dtype="int")

        condition[:, 0] = ttl[state == 1] / sf
        condition[:, 1] = ttl[state == -1] / sf

        conditions.append(condition)

    return conditions


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
        # Under 'processed - behavior' module add extracted on/off intervals
        conditions = intervals_from_traces(self.recording_extractor)
        mech_stim = TimeIntervals(
            name='MechanicalStimulus',
            description="Activation times inferred from TTL commands for mechanical stimulus."
        )
        laser_stim = TimeIntervals(
            name='LaserStimulus',
            description="Activation times inferred from TTL commands for cortical laser stimulus."
        )
        for j, table in enumerate([mech_stim, laser_stim]):
            for row in conditions[j]:
                table.add_row(dict(start_time=row[0], stop_time=row[1]))
        check_module(nwbfile, 'behavior', "Contains behavioral data.").add_data_interface(mech_stim)
        check_module(nwbfile, 'behavior', "Contains behavioral data.").add(laser_stim)

        if stub_test or self.subset_channels is not None:
            recording = self.subset_recording(stub_test=stub_test)
        else:
            recording = self.recording_extractor

        # Pressure values
        nwbfile.add_stimulus(
            TimeSeries(
                name='MechanicalPressure',
                data=H5DataIO(recording.get_traces(0), compression="gzip"),
                unit=self.recording_extractor._channel_smrxinfo[0]['unit'],
                conversion=recording.get_channel_property(0, 'gain'),
                rate=recording.get_sampling_frequency(),
                description="Pressure sensor attached to the mechanical stimulus used to repeatedly evoke spiking."
            )
        )
