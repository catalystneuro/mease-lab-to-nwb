"""
Functions to extract info and data from smrx files.
Example:
ch_info, f =  get_channel_info('M113_C4.smrx', 1)
data, f =  get_channel_data('M113_C4.smrx', 1)
"""
from sonpy import lib as sp


# Get the saved time and date (I don't think its the session_start_time)
# f.GetTimeDate()

def get_channel_info(fpath, i):
    f = sp.SonFile(fpath, True)
    if f.GetOpenError() != 0:
        print(f'Error opening file: {sp.GetErrorString(f.GetOpenError())}')
        return None, None

    if f.ChannelType(i) == sp.DataType.Off:
        print(f'Channel type: Off')
        return None, None

    ch_info = {
        'type': f.ChannelType(i),           # Get the channel kind
        'ch_number': f.PhysicalChannel(i),  # Get the physical channel number associated with this channel
        'title': f.GetChannelTitle(i),      # Get the channel title
        'rate': f.GetIdealRate(i),          # Get the requested channel rate
        'max_time': f.ChannelMaxTime(i),    # Get the time of the last item in the channel
        'divide': f.ChannelDivide(i),       # Get the waveform sample interval in file clock ticks
        'tim_base': f.GetTimeBase(),        # Get how many seconds there are per clock tick
        'scale': f.GetChannelScale(i),      # Get the channel scale
        'offset': f.GetChannelOffset(i),    # Get the channel offset
        'unit': f.GetChannelUnits(i),       # Get the channel units
        'y_range': f.GetChannelYRange(i),   # Get a suggested Y range for the channel
        'comment': f.GetChannelComment(i),  # Get the comment associated with a channel
        'size_bytes:': f.ChannelBytes(i),   # Get an estimate of the data bytes stored for the channel
    }

    return ch_info, f


def get_channel_data(fpath, i):
    f = sp.SonFile(fpath, True)
    if f.GetOpenError() != 0:
        print('Error opening file:', sp.GetErrorString(f.GetOpenError()))
        return None, None

    if f.ChannelType(i) == sp.DataType.Off:
        print(f'Channel type: Off')
        return None, None

    # Data storage and function finder
    DataReadFunctions = {
        sp.DataType.Adc: sp.SonFile.ReadInts,
        sp.DataType.EventFall: sp.SonFile.ReadEvents,
        sp.DataType.EventRise: sp.SonFile.ReadEvents,
        sp.DataType.EventBoth: sp.SonFile.ReadEvents,
        sp.DataType.Marker: sp.SonFile.ReadMarkers,
        sp.DataType.AdcMark: sp.SonFile.ReadWaveMarks,
        sp.DataType.RealMark: sp.SonFile.ReadRealMarks,
        sp.DataType.TextMark: sp.SonFile.ReadTextMarks,
        sp.DataType.RealWave: sp.SonFile.ReadFloats
    }

    data = DataReadFunctions[f.ChannelType(i)](
        f,
        i,
        int(f.ChannelMaxTime(i) / f.ChannelDivide(i)),
        0,
        f.ChannelMaxTime(i)
    )

    return data, f
