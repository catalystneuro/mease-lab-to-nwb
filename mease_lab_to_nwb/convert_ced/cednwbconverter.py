"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
from datetime import datetime
from typing import Optional

from nwb_conversion_tools import NWBConverter, CEDRecordingInterface
import spikeextractors as se
from pynwb import NWBHDF5IO

from .cedstimulusinterface import CEDStimulusInterface


def quick_write(ced_file_path: str, session_description: str, session_start: str, save_path: str,
                sorting: Optional[se.SortingExtractor] = None,
                recording_lfp: Optional[se.RecordingExtractor] = None,
                overwrite: bool = False):
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
            **nwbfile_kwargs
        )
    if recording_lfp is not None:
        se.NwbRecordingExtractor.write_recording(
            recording=recording_lfp,
            save_path=save_path,
            write_as_lfp=True
        )


class CEDNWBConverter(NWBConverter):
    data_interface_classes = dict(
        CEDRecording=CEDRecordingInterface,
        CEDStimulus=CEDStimulusInterface
    )

    def __init__(self, source_data):
        channel_info = CEDRecordingInterface.get_all_channels_info(source_data['CEDRecording']['file_path'])
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

    def run_conversion(self, metadata: dict, nwbfile_path: Optional[str] = None, save_to_file: bool = True,
                       conversion_options: Optional[dict] = None, overwrite: bool = False,
                       sorting: Optional[se.SortingExtractor] = None,
                       recording_lfp: Optional[se.RecordingExtractor] = None):
        """
        Build nwbfile object, auto-populate with minimal values if missing.

        Parameters
        ----------
        metadata : dict
        nwbfile_path : Optional[str], optional
        save_to_file : bool, optional
        conversion_options : Optional[dict], optional
        overwrite : bool, optional
        sorting : SortingExtractor, optional
            A SortingExtractor object to write to the NWBFile.
        recording_lfp : RecordingExtractor, optional
            A RecordingExtractor object to write to the NWBFile.
        """
        nwbfile = super().run_conversion(
            metadata=metadata,
            save_to_file=False,
            conversion_options=conversion_options
        )
        if sorting is not None:
            se.NwbSortingExtractor.write_sorting(
                    sorting=sorting,
                    nwbfile=nwbfile
            )
        if recording_lfp is not None:
            se.NwbRecordingExtractor.write_recording(
                    recording=recording_lfp,
                    nwbfile=nwbfile,
                    write_as_lfp=True
            )

        if save_to_file:
            if nwbfile_path is None:
                raise TypeError("A path to the output file must be provided, but nwbfile_path got value None")

            if Path(nwbfile_path).is_file() and not overwrite:
                mode = "r+"
            else:
                mode = "w"

            with NWBHDF5IO(nwbfile_path, mode=mode) as io:
                if mode == "r+":
                    nwbfile = io.read()

                io.write(nwbfile)
            print(f"NWB file saved at {nwbfile_path}!")
        else:
            return nwbfile
