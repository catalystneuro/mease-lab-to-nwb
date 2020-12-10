"""Authors: Cody Baker and Ben Dichter."""
from pathlib import Path
import toml
from datetime import datetime
from typing import Optional, Union
import numpy as np

from nwb_conversion_tools import NWBConverter
import spikeextractors as se

from .syntaloseventinterface import SyntalosEventInterface
from .syntalosimageinterface import SyntalosImageInterface
from .syntalosrecordinginterface import SyntalosRecordingInterface


class SyntalosNWBConverter(NWBConverter):
    """Primary conversion class for Syntalos."""

    data_interface_classes = dict(
        SyntalosEvent=SyntalosEventInterface,
        SyntalosImage=SyntalosImageInterface,
        SyntalosRecording=SyntalosRecordingInterface
    )

    def get_metadata(self):
        metadata = super().get_metadata()
        metadata['NWBFile'].update(
            institution="EMBL - Heidelberg",
            lab="Mease"
        )

        intan_folder_path = Path(self.data_interface_objects['SyntalosRecording'].source_data['folder_path'])
        session_id = [x for x in intan_folder_path.iterdir() if x.suffix == ".rhd"][0].stem
        session_start = datetime.strptime(session_id[-13:], "%y%m%d_%H%M%S")
        metadata['NWBFile'].update(
            session_start_time=session_start.astimezone(),
            session_id=session_id,
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
                       timestamps: Optional[Union[list, np.ndarray]] = None,
                       recording_lfp: Optional[se.RecordingExtractor] = None):
        if sorting is not None:
            nwbfile_kwargs = dict(
                session_description=metadata['NWBFile']['session_description'],
                session_id=metadata['NWBFile']['session_id'],
                session_start_time=metadata['NWBFile']['session_start_time']
            )
            se.NwbSortingExtractor.write_sorting(
                sorting=sorting,
                save_path=nwbfile_path,
                timestamps=timestamps,
                overwrite=overwrite,
                **nwbfile_kwargs
            )
        overwrite = False
        super().run_conversion(
            nwbfile_path=nwbfile_path,
            metadata=metadata,
            save_to_file=save_to_file,
            overwrite=overwrite,
            conversion_options=conversion_options
        )
        if recording_lfp is not None:
            se.NwbRecordingExtractor.write_recording(
                recording=recording_lfp,
                save_path=nwbfile_path,
                write_as_lfp=True
            )
