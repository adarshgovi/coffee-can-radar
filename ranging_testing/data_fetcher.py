from WF_SDK import device, scope, wavegen
from dash import dcc, html
import numpy as np
import pandas as pd
import time
import threading

# Shared global variables
latest_data = {
    "time": [], "ch1": [], "ch2": [], "fft_freqs": [], "fft_vals": [], "peak_distances": [],
    "peak_freq": 0, "peak_distance": 0, "ffts": [], "averaging_number": 10, "heat_map_size": 10
}
device_data = None
connected = False

# Constants for frequency-to-distance conversion
SPEED_OF_LIGHT = 3e8  # Example: Speed of wave in meters/second (adjust as needed)
BANDWIDTH = 250e6
CHIRP_DURATION = 0.02

def connect_device():
    global device_data, connected
    try:
        device_data = device.open()
        # wavegπen.generate(device_data, channel=1, function=wavegen.function.square, offset=2, frequency=2.5, amplitude=2)
        scope.open(device_data, sampling_frequency=100000, amplitude_range=10)
        scope.trigger(device_data, enable=True, source=scope.trigger_source.analog, channel=1, level=2, edge_rising=True)
        connected = True
        print("connected")
        return True
    except device.error as e:
        print(f"Device connection error: {e}")
        return False

def disconnect_device():
    global device_data, connected
    if connected:
        device.close(device_data)
        connected = False

def fetch_data():
    while True:
        if connected:
            # Retrieve averaging number and heat map size from latest_data
            averaging_number = latest_data["averaging_number"]
            heat_map_size = latest_data["heat_map_size"]

            # Record data
            channel_1, channel_2 = scope.concurrent_record(device_data)
            t = np.arange(len(channel_1)) / scope.data.sampling_frequency

            # Define the moving window size (e.g., 100 samples)
            window_size = 10

            # Iterate through the data with a moving window
            for i in range(len(channel_1) - window_size):
                if channel_1[i] < 2 and channel_1[i + window_size - 1] >= 2:
                    break
            pulse_start_index = i + window_size // 2
            pulse_end_index = i + int(CHIRP_DURATION * scope.data.sampling_frequency) + window_size // 2 + 500
            sq_wave = channel_1[pulse_start_index:pulse_end_index]
            receive_signal = channel_2[pulse_start_index:pulse_end_index]

            # Compute FFT
            fft_vals = np.abs(np.fft.fft(receive_signal))[:len(receive_signal) // 2]
            fft_freqs = np.fft.fftfreq(len(receive_signal), t[1] - t[0])[:len(receive_signal) // 2]
            mask = (fft_freqs < 5000)

            fft_freqs = fft_freqs[mask]
            fft_vals = fft_vals[mask]
            print(len(fft_vals))

            # Find peak frequency
            peak_index = np.argmax(fft_vals)
            peak_freq = fft_freqs[peak_index] if len(fft_freqs) > 0 else 0
            peak_distance = to_distance(peak_freq)
            # Update peak distances list
            latest_data["peak_distances"].append(peak_distance)
            if len(latest_data["peak_distances"]) > averaging_number:
                latest_data["peak_distances"].pop(0)

            # Compute average peak distance
            average_peak_distance = np.mean(latest_data["peak_distances"])

            # Update FFTs list
            latest_data["ffts"].append(fft_vals.tolist())
            if heat_map_size:
                if len(latest_data["ffts"]) > heat_map_size:
                    latest_data["ffts"].pop(0)

            # Store data
            latest_data["time"] = t
            latest_data["ch1"] = sq_wave
            latest_data["ch2"] = receive_signal
            latest_data["fft_freqs"] = fft_freqs.tolist()
            latest_data["fft_vals"] = fft_vals.tolist()
            latest_data["peak_freq"] = peak_freq
            latest_data["peak_distance"] = average_peak_distance

        time.sleep(0.5)
    else:
        print("not connected")

# Start background thread
threading.Thread(target=fetch_data, daemon=True).start()

def to_distance(frequency):
    return frequency * (CHIRP_DURATION * SPEED_OF_LIGHT / (2 * BANDWIDTH))

def get_latest_data():
    return latest_data["time"], latest_data["ch1"], latest_data["ch2"], latest_data["fft_freqs"], latest_data["fft_vals"], latest_data["ffts"]

def get_peak_data():
    return latest_data["peak_freq"], latest_data["peak_distance"]

def download_csv():
    df = pd.DataFrame({
        "Time (s)": latest_data["time"],
        "Channel 1 (V)": latest_data["ch1"],
        "Channel 2 (V)": latest_data["ch2"],
        "Frequency (Hz)": latest_data["fft_freqs"],
        "FFT Magnitude": latest_data["fft_vals"],
        "Peak Frequency (Hz)": [latest_data["peak_freq"]],
        "Peak Distance (m)": [latest_data["peak_distance"]]
    })
    return dcc.send_data_frame(df.to_csv, "oscilloscope_data.csv")

# Setter methods to update averaging_number and heat_map_size
def set_averaging_number(value):
    latest_data["averaging_number"] = value

def set_heat_map_size(value):
    latest_data["heat_map_size"] = value