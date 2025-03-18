from WF_SDK import device, scope, wavegen
import numpy as np

CHIRP_DURATION = 0.02

class ScopeInterface:
    def __init__(self):
        self.device_data = None
        self.connected = False

    def connect_device(self):
        try:
            self.device_data = device.open()
            self.connected = True
            return True
        except device.error as e:
            print(f"Device connection error: {e}")
            return False

    def disconnect_device(self):
        if self.connected:
            device.close(self.device_data)
            self.connected = False

    def configure_scope(self, sampling_frequency=100000, amplitude_range=10, trigger_level=2):
        scope.open(self.device_data, sampling_frequency=sampling_frequency, amplitude_range=amplitude_range)
        scope.trigger(self.device_data, enable=True, source=scope.trigger_source.analog, channel=1, level=trigger_level, edge_rising=True)
    
    def fetch_data(self):
        if self.connected:
            # Record data
            channel_1, channel_2 = scope.concurrent_record(self.device_data)
            t = np.arange(len(channel_1)) / scope.data.sampling_frequency

            return channel_1, channel_2, t