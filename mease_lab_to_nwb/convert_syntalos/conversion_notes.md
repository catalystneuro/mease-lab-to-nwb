# Notes on Syntalos part of mease-lab-to-nwb data mapping
## Open questions for Ben or Alessio are in straight braces []
## TODO items are in curly braces {}
## Currently working off of the "Latest Syntalos Recording _20200730" folder in the shared "Heidelberg data"

### NWBFile
* basic datetext information for the session_start_time is in the folder name.


### Subject
The subject_id is pulled from the main attributes.toml; no other subject information is easily found.


### Position (processed, not acquisition)
While they are not simple positional tracking time series, there are a number of videos contained in the folder; these are included as ImageSeries, and are recommended to be included in the same location as the NWBFile so that we simply include the "external_file" option when defining the ImageSeries, so as not to overload the NWBFile with all the movie information.

{Need to double check that the timestamps for the movies are synced with recording; also that this generalized to a list of multiple movies, and how that works with .}


### Events
LabeledEvents are read in from the .csv and are added to acquisition.


### LFP
Processed by SI.


### Sorted units
Processed by SI. Converted via PickleInterface


### Recording information
Uses Intan recording device/format. Raw data is in uint16 format, as it will be saved to the ElectricalSeries. A conversion factor will be attached to the ElectricalSeries to convert these into float32 when accessed, but to coerce to true uV one would need to offset it was well; trying to get this added to the nwb-schema, but for now the offset are attached as custom electrode columns.

{Alessio is investigating the tsync questions on the Intan side}
