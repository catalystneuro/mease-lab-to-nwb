from mease_lab_to_nwb import CEDNWBConverter
import pynwb
from pathlib import Path
import numpy as np
import pytest
import os
import mease_elabftw


def to_nwbfile(converter, filename):
    metadata = converter.get_metadata()
    conversion_options = converter.get_conversion_options()
    converter.run_conversion(
        metadata=metadata,
        nwbfile_path=filename,
        save_to_file=True,
        overwrite=False,
        conversion_options=conversion_options,
    )


@pytest.fixture
def mock_get_nwb_metadata(monkeypatch):
    monkeypatch.setattr(
        mease_elabftw, "get_nwb_metadata", mease_elabftw.nwb.get_sample_nwb_metadata
    )


def test_cednwbconverter_ttltest(tmp_path, mock_get_nwb_metadata):
    # read smrx file
    file_recording = str(
        (Path(__file__).parent / "data" / "TTLtest_17mW.smrx").resolve()
    )
    source_data = dict(
        CEDRecording=dict(file_path=file_recording),
        CEDStimulus=dict(file_path=file_recording),
        Elabftw=dict(experiment_id=1),
    )
    converter = CEDNWBConverter(source_data=source_data)
    rec_ids = source_data["CEDRecording"]["smrx_channel_ids"]
    assert len(rec_ids) == 128
    stim_ids = source_data["CEDStimulus"]["smrx_channel_ids"]
    assert len(stim_ids) == 3
    # convert to nwb
    file_nwb = str(tmp_path / "out.nwb")
    to_nwbfile(converter, file_nwb)
    # read nwb file
    io = pynwb.NWBHDF5IO(file_nwb, "r")
    nwbfile = io.read()
    # metadata
    assert nwbfile.fields["experimenter"] == ("Liam Keegan",)
    assert (
        nwbfile.fields["identifier"]
        == "20211001-8b6f100d66f4312d539c52620f79d6a503c1e2d1"
    )
    assert (
        nwbfile.fields["session_description"]
        == "test fake experiment with json metadata"
    )
    assert nwbfile.subject.fields["description"] == "test mouse"
    assert nwbfile.subject.fields["genotype"] == "Nt1Cre-ChR2-EYFP"
    assert nwbfile.subject.fields["subject_id"] == "xy1"
    assert nwbfile.subject.fields["weight"] == "0.002 kg"
    # laser trace
    assert len(nwbfile.stimulus) == 4
    laser = nwbfile.stimulus["17mW Laser"]
    assert type(laser) == pynwb.ogen.OptogeneticSeries
    assert len(laser.data) == 180180
    assert laser.starting_time == 0
    assert laser.rate == 30030.030030030033
    assert np.allclose(np.min(laser.data), 0, atol=1e-3)
    assert np.allclose(np.max(laser.data), 0.017)
    # laser stim (on/off for each individual pulse)
    laser_stim = nwbfile.stimulus["17mW LaserStimulus"]
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


def test_cednwbconverter_m365(tmp_path, mock_get_nwb_metadata):
    # read smrx file
    file_recording = str(
        (Path(__file__).parent / "data" / "m365_5.5mW_1sec.smrx").resolve()
    )
    source_data = dict(
        CEDRecording=dict(file_path=file_recording),
        CEDStimulus=dict(file_path=file_recording),
        Elabftw=dict(experiment_id=1),
    )
    converter = CEDNWBConverter(source_data=source_data)
    rec_ids = source_data["CEDRecording"]["smrx_channel_ids"]
    assert len(rec_ids) == 64
    stim_ids = source_data["CEDStimulus"]["smrx_channel_ids"]
    assert len(stim_ids) == 3
    # convert to nwb
    file_nwb = str(tmp_path / "out.nwb")
    to_nwbfile(converter, file_nwb)
    # read nwb file
    io = pynwb.NWBHDF5IO(file_nwb, "r")
    nwbfile = io.read()
    assert len(nwbfile.stimulus) == 4
    # laser trace
    laser = nwbfile.stimulus["5.5mW Laser"]
    assert type(laser) == pynwb.ogen.OptogeneticSeries
    assert len(laser.data) == 30030
    assert laser.starting_time == 0
    assert laser.rate == 30030.030030030033
    assert np.allclose(np.min(laser.data), 0, atol=5e-3)
    assert np.allclose(np.max(laser.data), 0.0055)
    # laser stim (on/off for each individual pulse)
    laser_stim = nwbfile.stimulus["5.5mW LaserStimulus"]
    assert type(laser_stim) == pynwb.misc.IntervalSeries
    assert len(laser_stim.data) == 0
    assert len(laser_stim.timestamps) == 0


def test_cednwbconverter_mech_laser(tmp_path, mock_get_nwb_metadata):
    # read smrx file
    file_recording = str(
        (Path(__file__).parent / "data" / "RhdD_H5_Mech+Laser.smrx").resolve()
    )
    source_data = dict(
        CEDRecording=dict(file_path=file_recording),
        CEDStimulus=dict(file_path=file_recording),
        Elabftw=dict(experiment_id=1),
    )
    converter = CEDNWBConverter(source_data=source_data)
    rec_ids = source_data["CEDRecording"]["smrx_channel_ids"]
    assert len(rec_ids) == 64
    stim_ids = source_data["CEDStimulus"]["smrx_channel_ids"]
    assert len(stim_ids) == 3
    # convert to nwb
    file_nwb = str(tmp_path / "out.nwb")
    to_nwbfile(converter, file_nwb)
    # read nwb file
    io = pynwb.NWBHDF5IO(file_nwb, "r")
    nwbfile = io.read()
    assert len(nwbfile.stimulus) == 4
    # laser trace
    laser = nwbfile.stimulus["?mW Laser"]
    assert type(laser) == pynwb.ogen.OptogeneticSeries
    assert len(laser.data) == 60060
    assert laser.starting_time == 0
    assert laser.rate == 30030.030030030033
    # laser stim (none in this smrx file)
    laser_stim = nwbfile.stimulus["?mW LaserStimulus"]
    assert type(laser_stim) == pynwb.misc.IntervalSeries
    assert len(laser_stim.data) == 0
    assert len(laser_stim.timestamps) == 0
    # mech trace
    mech = nwbfile.stimulus["MechanicalPressure"]
    assert type(mech) == pynwb.base.TimeSeries
    assert len(mech.data) == 60060
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
    assert traces.data.shape == (60060, 64)
    io.close()


def test_cednwbconverter_dual_laser(tmp_path, mock_get_nwb_metadata):
    # read smrx file
    file_recording = str(
        (
            Path(__file__).parent / "data" / "Dual_RhdD_H3__RhdC_H5_LaserOnly_99mW.smrx"
        ).resolve()
    )
    source_data = dict(
        CEDRecording=dict(file_path=file_recording),
        CEDStimulus=dict(file_path=file_recording),
        Elabftw=dict(experiment_id=1),
    )
    converter = CEDNWBConverter(source_data=source_data)
    rec_ids = source_data["CEDRecording"]["smrx_channel_ids"]
    # recording contains two probes
    assert len(rec_ids) == 128
    stim_ids = source_data["CEDStimulus"]["smrx_channel_ids"]
    assert len(stim_ids) == 3
    # convert to nwb
    file_nwb = str(tmp_path / "out.nwb")
    to_nwbfile(converter, file_nwb)
    # read nwb file
    io = pynwb.NWBHDF5IO(file_nwb, "r")
    nwbfile = io.read()
    assert len(nwbfile.stimulus) == 4
    # laser trace
    laser = nwbfile.stimulus["99mW Laser"]
    assert type(laser) == pynwb.ogen.OptogeneticSeries
    assert len(laser.data) == 30030
    assert laser.starting_time == 0
    assert laser.rate == 30030.030030030033
    assert np.allclose(np.min(laser.data), 0, atol=5e-3)
    assert np.allclose(np.max(laser.data), 0.099)
    # laser stim
    laser_stim = nwbfile.stimulus["99mW LaserStimulus"]
    assert type(laser_stim) == pynwb.misc.IntervalSeries
    assert len(laser_stim.data) == 20
    assert len(laser_stim.timestamps) == 20
    assert np.allclose(laser_stim.data[0:4], [1, -1, 1, -1])
    assert np.allclose(laser_stim.data[-4:], [1, -1, 1, -1])
    assert np.allclose(
        laser_stim.timestamps[0:4], [0.0021312, 0.0121545, 0.1021311, 0.1121544]
    )
    assert np.allclose(
        laser_stim.timestamps[-4:], [0.8021637, 0.8121537, 0.9021636, 0.9121536]
    )
    # mech trace
    mech = nwbfile.stimulus["MechanicalPressure"]
    assert type(mech) == pynwb.base.TimeSeries
    assert len(mech.data) == 30030
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
    assert traces.data.shape == (30030, 128)
    io.close()


def test_cednwbconverter_mech_laser_bifreq(tmp_path, mock_get_nwb_metadata):
    # read smrx file
    file_recording = str(
        (Path(__file__).parent / "data" / "H5_Mech_1Hz_10Hz.smrx").resolve()
    )
    source_data = dict(
        CEDRecording=dict(file_path=file_recording),
        CEDStimulus=dict(file_path=file_recording),
        Elabftw=dict(experiment_id=1),
    )
    converter = CEDNWBConverter(source_data=source_data)
    rec_ids = source_data["CEDRecording"]["smrx_channel_ids"]
    assert len(rec_ids) == 64
    stim_ids = source_data["CEDStimulus"]["smrx_channel_ids"]
    assert len(stim_ids) == 3
    # convert to nwb
    file_nwb = str(tmp_path / "out.nwb")
    to_nwbfile(converter, file_nwb)
    # read nwb file
    io = pynwb.NWBHDF5IO(file_nwb, "r")
    nwbfile = io.read()
    assert len(nwbfile.stimulus) == 4
    # laser trace
    laser = nwbfile.stimulus["?mW Laser"]
    assert type(laser) == pynwb.ogen.OptogeneticSeries
    assert len(laser.data) == 5555238  # note: actual length in smrx file is 5555556
    assert laser.starting_time == 0
    assert laser.rate == 30030.030030030033
    # laser stim
    laser_stim = nwbfile.stimulus["?mW LaserStimulus"]
    assert type(laser_stim) == pynwb.misc.IntervalSeries
    assert len(laser_stim.data) == 216
    assert len(laser_stim.timestamps) == 216
    assert np.allclose(laser_stim.data[0:4], [1, -1, 1, -1])
    assert np.allclose(laser_stim.data[-4:], [1, -1, 1, -1])
    assert np.allclose(
        laser_stim.timestamps[0:4], [64.9925424, 64.9975374, 65.9925414, 65.9975697]
    )
    assert np.allclose(
        laser_stim.timestamps[-4:], [174.8920995, 174.8970945, 174.9920994, 174.9970944]
    )
    # mech trace
    mech = nwbfile.stimulus["MechanicalPressure"]
    assert type(mech) == pynwb.base.TimeSeries
    assert len(mech.data) == 5555556
    assert mech.rate == 30030.030030030033
    assert mech.starting_time == 0
    # mech stim
    mech_stim = nwbfile.stimulus["MechanicalStimulus"]
    assert type(mech_stim) == pynwb.misc.IntervalSeries
    assert len(mech_stim.data) == 6
    assert len(mech_stim.timestamps) == 6
    assert np.allclose(mech_stim.data[:], [1, -1, 1, -1, 1, -1])
    assert np.allclose(
        mech_stim.timestamps[:],
        [4.9914369, 9.9914985, 64.9925424, 69.9925374, 124.99155, 129.9915117],
    )
    # traces
    assert len(nwbfile.acquisition) == 1
    traces = nwbfile.acquisition["ElectricalSeries_raw"]
    assert type(traces) == pynwb.ecephys.ElectricalSeries
    assert traces.data.shape == (
        5555238,
        64,
    )  # note: actual length in smrx file is 5555556
    io.close()
