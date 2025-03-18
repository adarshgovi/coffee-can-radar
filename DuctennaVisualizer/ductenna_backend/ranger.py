import numpy as np
import pandas as pd


class Ranger:
    def __init__(self, chirp_duration, bandwidth, sampling_frequency):
        self.chirp_duration = chirp_duration
        self.bandwidth = bandwidth
        self.sampling_frequency = sampling_frequency

    def get_first_pulse(self, ch1_data, ch2_data):
        # Find the first pulse in the data
        # For now, just return the first chirp and sync pulse
        chirp = ch1_data
        sync_pulse = ch2_data
        # Define the moving window size (e.g., 100 samples)
        window_size = 10

        # Iterate through the data with a moving window
        for i in range(len(ch1_data) - window_size):
            if ch1_data[i] < 2 and ch2_data[i + window_size - 1] >= 2:
                break
        pulse_start_index = i + window_size // 2

        pulse_end_index = pulse_start_index + int(self.chirp_duration * self.sampling_frequency) + 500
        return pulse_start_index, pulse_end_index
       
        return chirp, sync_pulse

    def get_distance(self, chirp):
        # Placeholder for distance calculation
        # For now, just return a random value
        distance = np.random.random()
        return distance