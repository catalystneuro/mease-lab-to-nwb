import numpy as np
from collections import defaultdict

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

    :param ts: The timestamp series
    :type ts: ndarray
    :param laser_power: the power of the laser in mw
    :type laser_power: int
    :return: The laser conditions dict
    :rtype: dict
    """

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
