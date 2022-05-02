from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile
import mease_elabftw


class ElabftwInterface(BaseDataInterface):
    """Data interface for importing experiment metadata from elabftw"""

    @classmethod
    def get_source_schema(cls):
        return dict(properties=dict(experiment_id=dict(type="number")))

    def get_metadata(self):
        experiment_id = self.source_data.get("experiment_id")
        if experiment_id is None:
            return {}
        metadata = mease_elabftw.get_nwb_metadata(experiment_id)
        # temporary hacks to pass schema validation
        del metadata["Other"]
        return metadata

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        return
