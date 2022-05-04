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
from collections import defaultdict


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


# approximate inequality operator: returns true if they differ by at least ~5%
def differ(a, b):
    return not np.isclose(a, b, rtol=0.05)


# convert measured interval to nearest unique_interval and return as string
def to_hz_str(interval, unique_intervals):
    return (
        f"{1.0/unique_intervals[(np.abs(unique_intervals - interval)).argmin()]:.3g}Hz"
    )


def get_frequencies(ts, laser_power):
    """
    Extract frequency information and frequency blocks from timestamp data.
    Currently the largest difference between our method and theirs is 3.33 e-5 s

    :param ts: The timestamp series. either an ndarray or a pynwb.misc.IntervalSeries in seconds.
    :type ts: ndarray or pynwb.misc.IntervalSeries
    :param laser_power: the power of the laser in mw
    :type laser_power: int
    :return: The laser conditions dict
    :rtype: dict
    """

    if isinstance(ts, IntervalSeries):
        ts = ts.timestamps[:]

    dts = np.diff(ts)
    times = ts[0::2]
    pulses = dts[0::2]
    intervals = ts[2::2] - ts[0:-2:2]

    # enumerate possible intervals (rounding to nearest 1/10 of smallest interval)
    interval_res = 0.1 * np.min(intervals)
    unique_intervals, unique_interval_counts = np.unique(
        np.round(intervals / interval_res) * interval_res, return_counts=True
    )
    # print("interval:",unique_intervals)
    pulse_res = 0.1 * np.min(pulses)
    unique_pulses, unique_pulse_counts = np.unique(
        np.round(pulses / pulse_res) * pulse_res, return_counts=True
    )

    # collect pulses into contiguous chunks of the same frequency

    # note: interval of zero is a continuous laser pulse
    conditions = defaultdict(list)

    i0 = 0
    t0 = 0
    n0 = 0
    current_freq = None
    for t, p, i in zip(times, pulses, intervals):
        conditions["Laser_AllTriggers"].append([t, p])
        # print(t, p, i)
        if i0 == 0:
            t0 = t
            p0 = p
            i0 = i
            n0 = 0
            # print(f"starting at {t0} with pulse {p0}, intervals {i0}")
        elif differ(p, p0) or differ(i, i0):
            if n0 == 1:
                current_freq = f"{int(np.round(p0))}sec_pulse"
                # single pulse -> start/stop times for continuous pulse
                # print(f"single pulse -> continuous pulse {t0} -> {p0}")
                conditions[f"Laser_{current_freq}_{laser_power}mW_Block"].append(
                    (t0, p0)
                )
                t0 = t
                p0 = p
                i0 = i
                n0 = 0
                #  print(f"starting at {t0} with pulse {p0}, intervals {i0}")
            else:
                current_freq = to_hz_str(i0, unique_intervals)
                # multiple pulses -> start/stop times for fixed frequency pulse
                #  print(f"ending at {t-t0+p} after {n0} pulses with interval {i0}")
                conditions[f"Laser_{current_freq}_{laser_power}mW_Block"].append(
                    (t0, t - t0 + p)
                )

                i0 = 0

        n0 = n0 + 1

    # deal with last pulse
    # print(f"finishing last pulse")
    if i0 == 0:
        # final single pulse -> start/stop times for continuous pulse
        # print(f"single pulse -> continuous pulse {times[-1]} -> {pulses[-1]}")
        current_freq = f"{int(np.round(pulses[-1]))}sec_pulse"
        conditions[f"Laser_{current_freq}_{laser_power}mW_Block"].append(
            (times[-1], pulses[-1])
        )
    else:
        # multiple pulses -> start/stop times for fixed frequency pulse
        current_freq = to_hz_str(i0, unique_intervals)
        conditions[f"Laser_{current_freq}_{laser_power}mW_Block"].append(
            (t0, times[-1] - t0 + p0)
        )

    for condition in conditions.values():
        condition = np.asarray(condition)

    return conditions


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
