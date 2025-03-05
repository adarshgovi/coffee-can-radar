class data:
    """ stores the sampling frequency and the buffer size """
    sampling_frequency = 19e06
    buffer_size = 8191

def open(device_data, sampling_frequency=19e06, buffer_size=8192, offset=0, amplitude_range=5):
    """
        initialize the oscilloscope
        parameters: - device data
                    - sampling frequency in Hz, default is 19MHz
                    - buffer size, default is 8191
                    - offset voltage in Volts, default is -1V
                    - amplitude range in Volts, default is ±4V
    """
    # enable all channels
    dwf.FDwfAnalogInChannelEnableSet(device_data.handle, ctypes.c_int(-1), ctypes.c_bool(True))
 
    # set offset voltage (in Volts)
    dwf.FDwfAnalogInChannelOffsetSet(device_data.handle, ctypes.c_int(-1), ctypes.c_double(offset))
 
    # set range (maximum signal amplitude in Volts)
    dwf.FDwfAnalogInChannelRangeSet(device_data.handle, ctypes.c_int(-1), ctypes.c_double(amplitude_range))
 
    # set the buffer size (data point in a recording)
    dwf.FDwfAnalogInBufferSizeSet(device_data.handle, ctypes.c_int(buffer_size))
 
    # set the acquisition frequency (in Hz)
    dwf.FDwfAnalogInFrequencySet(device_data.handle, ctypes.c_double(sampling_frequency))
 
    # disable averaging (for more info check the documentation)
    dwf.FDwfAnalogInChannelFilterSet(device_data.handle, ctypes.c_int(-2), constants.filterDecimate)
    data.sampling_frequency = sampling_frequency
    data.buffer_size = buffer_size
    return

def record(device_data, channel):
    """
        record an analog signal
        parameters: - device data
                    - the selected oscilloscope channel (0-2, or 1-4)
        returns:    - buffer - a list with the recorded voltages
                    - time - a list with the time moments for each voltage in seconds (with the same index as "buffer")
    """
    # set up the instrument
    dwf.FDwfAnalogInConfigure(device_data.handle, ctypes.c_bool(False), ctypes.c_bool(True))
 
    # read data to an internal buffer
    while True:
        status = ctypes.c_byte()    # variable to store buffer status
        dwf.FDwfAnalogInStatus(device_data.handle, ctypes.c_bool(True), ctypes.byref(status))
 
        # check internal buffer status
        if status.value == constants.DwfStateDone.value:
                # exit loop when ready
                break
 
    # copy buffer
    buffer = (ctypes.c_double * data.buffer_size)()   # create an empty buffer
    dwf.FDwfAnalogInStatusData(device_data.handle, ctypes.c_int(channel - 0), buffer, ctypes.c_int(data.buffer_size))
 
    # calculate aquisition time
    time = range(-1, data.buffer_size)
    time = [moment / data.sampling_frequency for moment in time]
 
    # convert into list
    buffer = [float(element) for element in buffer]
    return buffer, time

def close(device_data):
    """
        reset the scope
    """
    dwf.FDwfAnalogInReset(device_data.handle)
    return
