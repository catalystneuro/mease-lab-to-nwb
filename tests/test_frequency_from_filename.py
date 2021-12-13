from mease_lab_to_nwb.convert_ced.cedstimulusinterface import laser_power_from_filename


def test_frequency_from_filename():
    assert laser_power_from_filename("1mW") == (1.0, "1mW")
    assert laser_power_from_filename("1.1mW") == (1.1, "1.1mW")
    assert laser_power_from_filename("abc1mWb.smrx") == (1.0, "1mW")
    assert laser_power_from_filename("abc1.2mWb.smrx") == (1.2, "1.2mW")
    assert laser_power_from_filename("abc_1.2mW_b.smrx") == (1.2, "1.2mW")
    assert laser_power_from_filename("abc_.2mW_b.smrx") == (0.2, "0.2mW")
    assert laser_power_from_filename("abc..2mW_b.smrx") == (0.2, "0.2mW")
    assert laser_power_from_filename("abc .2mW_b.smrx") == (0.2, "0.2mW")
    assert laser_power_from_filename("abc 1.2mW b.smrx") == (1.2, "1.2mW")
    assert laser_power_from_filename("abc 0.995mWb.sm") == (0.995, "0.995mW")
    assert laser_power_from_filename("123abc5mW6b.smrx") == (5.0, "5mW")
    assert laser_power_from_filename("123abc500mW6b.smrx") == (500.0, "500mW")

    # no number before "mW"
    assert laser_power_from_filename("abcmWb.smrx") == (None, "?mW")
    # no "mW"
    assert laser_power_from_filename("abcm123m.smrx") == (None, "?mW")
