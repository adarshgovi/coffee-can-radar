import numpy as np
import pandas as pd


class Ranger:
    def __init__(self, chirp_duration, bandwidth, sampling_frequency):
        self.chirp_duration = chirp_duration
        self.bandwidth = bandwidth
        self.sampling_frequency = sampling_frequency

    def get_first_pulse(self, sync_pulse):
        # Find the first pulse in the data
        window_size = 10

        # Iterate through the data with a moving window
        for i in range(len(sync_pulse) - window_size):
            if sync_pulse[i] < 2 and sync_pulse[i + window_size - 1] >= 2:
                break
        pulse_start_index = i + (window_size // 2)+7

        pulse_end_index = pulse_start_index + int(self.chirp_duration * self.sampling_frequency) -3
        return pulse_start_index, pulse_end_index

    def get_distances(self, chirp):
        # Compute FFT
        fft_vals = np.abs(np.fft.fft(chirp))[:len(chirp) // 2]
        fft_freqs = np.fft.fftfreq(len(chirp), 1 / self.sampling_frequency)[:len(chirp) // 2]
        # fft_freqs = fft_freqs.tolist()
        # fft_vals = fft_vals.tolist()
        distances = self.to_distance(fft_freqs)
        return distances, fft_freqs, fft_vals
    
    def to_distance(self, frequency):
        return frequency*(self.chirp_duration * 3e8 / (2 * self.bandwidth))

    def get_peak_distance(self, distances):
        peak_index = np.argmax(distances)
        peak_freq = distances[peak_index] if len(distances) > 0 else 0
        peak_distance = self.to_distance(peak_freq)
        return peak_distance