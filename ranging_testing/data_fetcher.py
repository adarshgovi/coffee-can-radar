from WF_SDK import device, scope
import numpy as np
import pandas as pd
import time
import threading

# Shared global variables
latest_data = {
    "time": [], "ch1": [], "ch2": [], "fft_freqs": [], "fft_vals": [],
    "peak_freq": 0, "peak_distance": 0
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
        scope.open(device_data, sampling_frequency=100000)
        scope.trigger(device_data, enable=True, source=scope.trigger_source.analog, channel=2, level=2, edge_rising=True)
        connected = True
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
            channel_1, channel_2 = scope.concurrent_record(device_data)
            t = np.arange(len(channel_1)) / scope.data.sampling_frequency

            # find rising edge for channel 2
            # rising_edge = np.argmax(channel_2 > 0.5)
            # channel_1 = channel_1[rising_edge:]
            # channel_2 = channel_2[rising_edge:]
            # t = t[rising_edge:]


            # Compute FFT
            fft_vals = np.abs(np.fft.fft(channel_1))[:len(channel_1)//2]
            fft_freqs = np.fft.fftfreq(len(channel_1), t[1] - t[0])[:len(channel_1)//2]
            # get frequencies up to 1000 Hz and greater than 0
            mask = (fft_freqs < 5000)

            fft_freqs = fft_freqs[mask]
            fft_vals = fft_vals[mask]
            print(fft_freqs)
            
            # # Find peak frequency
            peak_index = np.argmax(fft_vals)  # Index of max FFT magnitude
            # print(peak_index)
            peak_freq = fft_freqs[peak_index] if len(fft_freqs) > 0 else 0  # Handle empty case
            # print(peak_freq)
            # Convert frequency to distance
            peak_distance = (peak_freq * CHIRP_DURATION * SPEED_OF_LIGHT/(2*BANDWIDTH)) * FREQ_TO_DIST_SCALING if peak_freq > 0 else 0
            # peak_distance, peak_freq = 48.828, 0.586 
            # Store data
            latest_data["time"] = t
            latest_data["ch1"] = channel_1
            latest_data["ch2"] = channel_2
            latest_data["fft_freqs"] = fft_freqs.tolist()
            latest_data["fft_vals"] = fft_vals.tolist()
            latest_data["peak_freq"] = peak_freq
            latest_data["peak_distance"] = peak_distance

        time.sleep(0.5)

# Start background thread
threading.Thread(target=fetch_data, daemon=True).start()

def get_latest_data():
    return latest_data["time"], latest_data["ch1"], latest_data["ch2"], latest_data["fft_freqs"], latest_data["fft_vals"]

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
