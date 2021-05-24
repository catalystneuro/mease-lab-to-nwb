"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
from datetime import datetime
from typing import Optional

import spikeextractors as se
from pynwb import NWBHDF5IO
from nwb_conversion_tools import NWBConverter, CEDRecordingInterface
from nwb_conversion_tools.utils.spike_interface import write_recording

from .cedstimulusinterface import CEDStimulusInterface


def quick_write(
    ced_file_path: str, 
    session_description: str, 
    session_start: str, 
    save_path: str,
    sorting: Optional[se.SortingExtractor] = None,
    recording_lfp: Optional[se.RecordingExtractor] = None,
    overwrite: bool = False
):
    """Automatically extracts required session info from ced_file_path and writes NWBFile in spikeextractors."""
    ced_file_path = Path(ced_file_path)
    session_id = ced_file_path.stem
    nwbfile_kwargs = dict(
        session_description=session_description,
        session_start_time=session_start.astimezone(),
        session_id=session_id,
    )
    if sorting is not None:
        se.NwbSortingExtractor.write_sorting(
            sorting=sorting,
            save_path=save_path,
            overwrite=overwrite,
            skip_properties=['mda_max_channel'],
            skip_features=['waveforms'],
            **nwbfile_kwargs
        )
    if recording_lfp is not None:
        write_recording(
            recording=recording_lfp,
            save_path=save_path,
            write_as='lfp'
        )


class CEDNWBConverter(NWBConverter):
    data_interface_classes = dict(
        CEDRecording=CEDRecordingInterface,
        CEDStimulus=CEDStimulusInterface
    )

    def __init__(self, source_data):
        channel_info = self.data_interface_classes['CEDRecording'].RX.get_all_channels_info(
            source_data['CEDRecording']['file_path']
        )
        rhd_channels = []
        stim_channels = []
        for ch, info in channel_info.items():
            if "Rhd" in info['title']:
                rhd_channels.append(ch)
            if info['title'] in ["CED_Mech", "MechTTL", "Laser"]:
                stim_channels.append(ch)
        source_data['CEDRecording'].update(smrx_channel_ids=rhd_channels)
        source_data['CEDStimulus'].update(smrx_channel_ids=stim_channels)
        super().__init__(source_data)

    def get_metadata(self):
        metadata = super().get_metadata()
        smrx_file_path = Path(self.data_interface_objects['CEDRecording'].source_data['file_path'])
        session_id = smrx_file_path.stem
        metadata['NWBFile'].update(
            institution="EMBL - Heidelberg",
            lab="Mease",
            session_id=session_id
        )
        return metadata