from WF_SDK import device, scope, wavegen, tools, error   # import instruments
import matplotlib.pyplot as plt   # needed for plotting
import matplotlib
# matplotlib.use('TkAgg')
from time import sleep     

if __name__ == "__main__":
    # Open the device
    try: 
        device_data = device.open()
    except device.error as e:
        print(e)
        exit(1)
    
    print(device_data.name)
    scope.open(device_data)   # open the scope
    # set up triggering on scope channel 1
    scope.trigger(device_data, enable=True, source=scope.trigger_source.analog, channel=2, level=0, edge_rising=True)
    # record data with the scope on channel 1
    buffer = scope.record(device_data, channel=2)

    # limit displayed data size
    # length = len(buffer)
    # buffer = buffer[0:length]

    print("Buffer length: ", len(buffer))

    # generate buffer for time moments
    time = []
    for index in range(len(buffer)):
        time.append(index * 1e03 / scope.data.sampling_frequency)   # convert time to ms

    # plot
    plt.plot(time, buffer)
    plt.xlabel("time [ms]")
    plt.ylabel("voltage [V]")
    plt.show()

    



