"""Authors: Cody Baker and Alessio Buccino."""
import numpy as np
import re

from pynwb import NWBFile, TimeSeries
from pynwb.misc import IntervalSeries
from pynwb.ogen import OptogeneticSeries, OptogeneticStimulusSite
from pynwb.device import Device
from hdmf.backends.hdf5.h5_utils import H5DataIO
from nwb_conversion_tools.datainterfaces.ecephys.baserecordingextractorinterface import (
    BaseRecordingExtractorInterface,
)
from nwb_conversion_tools.utils.json_schema import get_schema_from_method_signature
from spikeextractors import RecordingExtractor, CEDRecordingExtractor


def laser_power_from_filename(filename: str):
    """Extract laser power from smrx filename

    Returns float and string representations of laser power extracted from filename.
    Assumes filename of form "*[optional numbers][optional .][at least 1 number]mW*".
    """
    # search for
    m = re.search(r"([0-9]*\.?[0-9]+)mW", filename)
    if m:
        mw = float(m.group(1))
        return mw, f"{mw:g}mW"
    return None, "?mW"


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


def intervals_from_traces(
    name: str, description: str, recording: RecordingExtractor, channel_id: int
):
    """Extract interval times from TTL pulses.

    Returns an IntervalSeries with an interval for each TTL pulse.
    See https://pynwb.readthedocs.io/en/stable/pynwb.misc.html?highlight=intervalseries#pynwb.misc.IntervalSeries

    Uses a heuristic to detect when TTL data was not collected (and signal is just zero + noise):
    if the fraction of points outside the upper/lower quartiles is too low, returns empty arrays.
    This avoids conversion of pure noise into a huge number of spurious intervals.
    """
    interval_series = IntervalSeries(name, description, data=[], timestamps=[])
    tr = recording.get_traces(channel_id)[0]
    dt = 1.0 / recording.get_sampling_frequency()

    min_value = np.amin(tr)
    peak_to_peak = np.ptp(tr)
    threshold = min_value + 0.5 * peak_to_peak
    n_upper_quartile = np.sum(tr > min_value + 0.75 * peak_to_peak)
    n_lower_quartile = np.sum(tr < min_value + 0.25 * peak_to_peak)
    fraction = (n_upper_quartile + n_lower_quartile) / len(tr)
    if fraction < 0.75:
        print(
            f"Fraction of points in upper/lower quartiles too low: {fraction}. Assuming there is no TTL pulse data."
        )
        return interval_series
    i = 0
    n = len(tr)
    while i < n and tr[i] > threshold:
        i = i + 1
    if i > 0:
        print(f"Warning: trace starts above threshold - skipped first {i} points")
    try:
        while i < n:
            while tr[i] <= threshold:
                i = i + 1
            interval_start = i * dt
            while tr[i] > threshold:
                i = i + 1
            interval_stop = i * dt
            interval_series.add_interval(interval_start, interval_stop)
    except IndexError:
        assert i == len(tr)
    return interval_series


class CEDStimulusInterface(BaseRecordingExtractorInterface):
    """Primary data interface class for converting CED mechanical and cortical laser stimuli."""

    RX = CEDRecordingExtractor

    @classmethod
    def get_source_schema(cls):
        source_schema = get_schema_from_method_signature(
            class_method=cls.RX.__init__, exclude=["smrx_channel_ids"]
        )
        source_schema.update(additionalProperties=True)
        source_schema["properties"].update(
            file_path=dict(
                type=source_schema["properties"]["file_path"]["type"],
                format="file",
                description="path to data file",
            ),
        )
        return source_schema

    def run_conversion(
        self, nwbfile: NWBFile, metadata: dict = None, stub_test: bool = False
    ):
        nwbfile.add_stimulus(
            intervals_from_traces(
                "MechanicalStimulus",
                "Activation times inferred from TTL commands for mechanical stimulus.",
                self.recording_extractor,
                1,
            )
        )
        laser_power_mw, laser_power_str = laser_power_from_filename(
            self.recording_extractor._kwargs["file_path"]
        )
        nwbfile.add_stimulus(
            intervals_from_traces(
                f"{laser_power_str} LaserStimulus",
                "Activation times inferred from TTL commands for cortical laser stimulus.",
                self.recording_extractor,
                2,
            )
        )

        if stub_test or self.subset_channels is not None:
            recording = self.subset_recording(stub_test=stub_test)
        else:
            recording = self.recording_extractor

        # Pressure values
        nwbfile.add_stimulus(
            TimeSeries(
                name="MechanicalPressure",
                data=H5DataIO(recording.get_traces(0).T, compression="gzip"),
                unit=self.recording_extractor._channel_smrxinfo[0]["unit"],
                conversion=recording.get_channel_property(0, "gain"),
                rate=recording.get_sampling_frequency(),
                description="Pressure sensor attached to the mechanical stimulus used to repeatedly evoke spiking.",
            )
        )

        # Laser as optogenetic stimulus
        ogen_device = nwbfile.create_device(
            name="ogen_device", description="ogen description"
        )
        ogen_site = OptogeneticStimulusSite(
            name="name",
            device=ogen_device,
            description="description",
            excitation_lambda=1.0,
            location="location",
        )

        laser_trace = recording.get_traces(2)[0]
        if laser_power_mw:
            # rescale laser trace
            max_laser_trace = np.max(laser_trace)
            laser_trace *= 0.001 * laser_power_mw / max_laser_trace
        nwbfile.add_ogen_site(ogen_site)
        nwbfile.add_stimulus(
            OptogeneticSeries(
                name=f"{laser_power_str} Laser",
                data=laser_trace,
                site=ogen_site,
                rate=recording.get_sampling_frequency(),
                description="Laser TTL.",
            )
        )
