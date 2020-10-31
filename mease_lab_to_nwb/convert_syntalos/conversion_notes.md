# Notes on Syntalos part of mease-lab-to-nwb data mapping
## Open questions for Ben or Alessio are in straight braces []
## TODO items are in curly braces {}
## Currently working off of the "Latest Syntalos Recording _20200730" folder in the shared "Heidelberg data"

### NWBFile
* basic datetext information for the session_start_time is in the folder name.


### Subject
?


### Position (processed, not acquisition)
While they are not simple positional tracking time series, there are a number of videos contained in the folder; these can be included as ImageSeries, and are recommended to be included in the same location as the NWBFile so that we simply include the "external_file" option when defining the ImageSeries, so as not to overload the NWBFile with all the movie information.


### Intervals
?


### LFP
?


### Sorted units
?


### Recording information
Uses Intan recording device/format.
{Need to add interface to nwb-conversion-tools or use Ben's suggested auto-class creation function. Also need to test on data, ensure it looks OK on the RecordingExtractor side.}
