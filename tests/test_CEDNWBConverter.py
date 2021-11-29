from mease_lab_to_nwb import CEDNWBConverter
import pynwb
from pathlib import Path
import numpy as np
import pytest
import os


def test_cednwbconverter(tmp_path):
    # read smrx file
    file_recording = str((Path(__file__).parent / "data" / "TTLtest.smrx").resolve())
    source_data = dict(
        CEDRecording=dict(file_path=file_recording),
        CEDStimulus=dict(file_path=file_recording),
    )
    converter = CEDNWBConverter(source_data=source_data)
    rec_ids = source_data["CEDRecording"]["smrx_channel_ids"]
    assert len(rec_ids) == 128
    stim_ids = source_data["CEDStimulus"]["smrx_channel_ids"]
    assert len(stim_ids) == 3
    # convert to nwb
    file_nwb = str(tmp_path / "test.nwb")
    metadata = converter.get_metadata()
    conversion_options = converter.get_conversion_options()
    converter.run_conversion(
        metadata=metadata,
        nwbfile_path=file_nwb,
        save_to_file=True,
        overwrite=False,
        conversion_options=conversion_options,
    )
    # read nwb file
    io = pynwb.NWBHDF5IO(file_nwb, "r")
    nwbfile = io.read()
    assert len(nwbfile.stimulus) == 4
    # laser trace
    laser = nwbfile.stimulus["Laser"]
    assert type(laser) == pynwb.ogen.OptogeneticSeries
    assert len(laser.data) == 180180
    assert laser.starting_time == 0
    assert laser.rate == 30030.030030030033
    # laser stim (on/off for each individual pulse)
    laser_stim = nwbfile.stimulus["LaserStimulus"]
    assert type(laser_stim) == pynwb.misc.IntervalSeries
    assert len(laser_stim.data) == 102
    assert len(laser_stim.timestamps) == 102
    assert np.allclose(laser_stim.data[0:4], [1, -1, 1, -1])
    assert np.allclose(laser_stim.data[-4:], [1, -1, 1, -1])
    assert np.allclose(
        laser_stim.timestamps[0:4], [0.6022971, 0.6123204, 0.7023303, 0.7123203]
    )
    assert np.allclose(
        laser_stim.timestamps[-4:], [5.5023921, 5.5123821, 5.602392, 5.612382]
    )
    # mech trace
    mech = nwbfile.stimulus["MechanicalPressure"]
    assert type(mech) == pynwb.base.TimeSeries
    assert len(mech.data) == 180180
    assert mech.rate == 30030.030030030033
    assert mech.starting_time == 0
    # mech stim (none in this smrx file)
    mech_stim = nwbfile.stimulus["MechanicalStimulus"]
    assert type(mech_stim) == pynwb.misc.IntervalSeries
    assert len(mech_stim.data) == 0
    assert len(mech_stim.timestamps) == 0
    # traces
    assert len(nwbfile.acquisition) == 1
    traces = nwbfile.acquisition["ElectricalSeries_raw"]
    assert type(traces) == pynwb.ecephys.ElectricalSeries
    assert traces.data.shape == (180180, 128)
    io.close()
