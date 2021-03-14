"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
import toml
from datetime import datetime
from typing import Optional, Union
import numpy as np

from nwb_conversion_tools import NWBConverter
import spikeextractors as se
from pynwb import NWBHDF5IO

from .syntaloseventinterface import SyntalosEventInterface
from .syntalosimageinterface import SyntalosImageInterface
from .syntalosrecordinginterface import SyntalosRecordingInterface

OptionalArrayType = Optional[Union[list, np.ndarray]]


def quick_write(intan_folder_path: str, session_description: str, save_path: str,
                sorting: Optional[se.SortingExtractor] = None,
                recording_lfp: Optional[se.RecordingExtractor] = None,
                use_times: bool = True, overwrite: bool = False):
    """Automatically extracts required session info from intan_folder_path and writes NWBFile in spikeextractors."""
    intan_folder_path = Path(intan_folder_path)
    session_id = [x for x in intan_folder_path.iterdir() if x.suffix == ".rhd"][0].stem
    session_start = datetime.strptime(session_id[-13:], "%y%m%d_%H%M%S")
    nwbfile_kwargs = dict(
        session_description=session_description,
        session_start_time=session_start.astimezone(),
        session_id=session_id,
    )
    if sorting is not None:
        se.NwbSortingExtractor.write_sorting(
            sorting=sorting,
            save_path=save_path,
            use_times=use_times,
            overwrite=overwrite,
            **nwbfile_kwargs
        )
    if recording_lfp is not None:
        se.NwbRecordingExtractor.write_recording(
            recording=recording_lfp,
            save_path=save_path,
            write_as_lfp=True
        )


class SyntalosNWBConverter(NWBConverter):
    """Primary conversion class for Syntalos."""

    data_interface_classes = dict(
        SyntalosEvent=SyntalosEventInterface,
        SyntalosImage=SyntalosImageInterface,
        SyntalosRecording=SyntalosRecordingInterface
    )

    def get_metadata(self):
        metadata = super().get_metadata()
        intan_folder_path = Path(self.data_interface_objects['SyntalosRecording'].source_data['folder_path'])
        session_id = [x for x in intan_folder_path.iterdir() if x.suffix == ".rhd"][0].stem
        session_start = datetime.strptime(session_id[-13:], "%y%m%d_%H%M%S")
        metadata['NWBFile'].update(
            institution="EMBL - Heidelberg",
            lab="Mease",
            session_id=session_id,
            session_start_time=session_start.astimezone()
        )
        main_attr_file = intan_folder_path.parent / "attributes.toml"
        if main_attr_file.is_file():
            metadata.update(
                Subject=dict(
                    subject_id=toml.load(main_attr_file)['subject_id']
                )
            )

        return metadata

    def run_conversion(self, metadata: dict, nwbfile_path: Optional[str] = None, save_to_file: bool = True,
                       conversion_options: Optional[dict] = None, overwrite: bool = False,
                       sorting: Optional[se.SortingExtractor] = None,
                       recording_lfp: Optional[se.RecordingExtractor] = None,
                       use_times: bool = True):
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
        use_times : bool
            If True, tsync timestamps are written to NWB.
        """
        nwbfile = super().run_conversion(
            metadata=metadata,
            save_to_file=False,
            conversion_options=conversion_options
        )
        if sorting is not None:
            se.NwbSortingExtractor.write_sorting(
                    sorting=sorting,
                    nwbfile=nwbfile,
                    use_times=use_times
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
