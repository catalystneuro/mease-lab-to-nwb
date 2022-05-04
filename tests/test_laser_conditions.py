import pytest
import numpy as np
import mat73
from mease_lab_to_nwb.get_laser_conditions import get_frequencies


def test_get_frequencies():

    # import timestamps
    ts = np.load("tests/data/timestamp_test.npy")

    # import control data
    data_dict = mat73.loadmat("tests/data/test_m6pt2and3_analysis.mat")
    names = data_dict["Conditions"]["name"]
    triggers = data_dict["Conditions"]["Triggers"]
    t0 = 0
    for trigger, name in zip(triggers, names):
        trigger[:] = trigger[:] / 30030.030030030033
        if "Block" in name:
            if t0 == 0:
                t0 = trigger[0, 0]
                trigger[:, 1] = trigger[:, 1] - trigger[:, 0]

                trigger[:, 0] = trigger[:, 0] - t0

            else:
                trigger[:, 1] = trigger[:, 1] - trigger[:, 0]
                trigger[:, 0] = trigger[:, 0] - t0

    compare_data = {name: trigger for (name, trigger) in zip(names, triggers)}

    # calculate laser frequencies

    data = get_frequencies(ts, 4)
    for condition in data.values():
        condition = np.asarray(condition)

    for key in data.keys():
        if key != "Laser_AllTriggers":
            data[key] = np.asarray(data[key])
            max_difference = np.max(np.abs(data[key][:, 0] - compare_data[key][:, 0]))
            min_difference = np.min(np.abs(data[key][:, 0] - compare_data[key][:, 0]))
            assert (max_difference - min_difference) < 5e-5
