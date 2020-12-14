# mease-lab-to-nwb

* CED processing through SpikeInterface
* CED conversion to NWB (under construction)
* Syntalos processing through SpikeInterface
* Syntalos conversion to NWB (under construction)

## Installation
```bash
pip install https://github.com/catalystneuro/mease-lab-to-nwb.git
```


# How to use - Syntalos

There are two ways to go about converting data from the Syntalos format.

The first is through the primary processing pipeline; the notebook `syntalos_spikeinterface_pipeline.ipynb`. This pipeline demonstrates how to read the intan signals through the custom extractor, perform post-processing such as LFP extraction, and run common spike sorters on these signals. It also supports further forms of sorting curation based on automated metrics, manual curation via `phy`, as well as ensemble methods (agreement between sorting algorithms). At the end of the pipeline, the user may either chose to save only the spike sorted data and LFP (quick-save), or to include the event table and videos as well (full conversion).

The second is shown by example in the convert_syntalos.py script, and will convert the raw intan signals without LFP processing or spike sorting. It will also convert the events table and videos as `ImageSeries` objects, which are stored externally and must therefore be submitted alongside the NWBFile when uploaded to DANDI. This script operates on an NWBFile in append mode by default, and thus may be used to complete a partial conversion that began with a quick-save in the processing pipeline.

The required arguments for the use of the relevant functions are denoted in the comments of their respective sections of both the pipeline and external conversion script. These include the file or folder locations of the data to be converted to NWB format, as well as several optional fields such as Subject information (species/age/weight).
