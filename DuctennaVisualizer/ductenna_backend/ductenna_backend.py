import redis
import time
import json
import numpy as np
import scope_interface
import ranger
import duct_datalogger

# constants 
SPEED_OF_LIGHT = 3e8
BANDWIDTH = 250e6
CHIRP_DURATION = 0.02
SAMPLING_FREQUENCY = 100000

if __name__ == "__main__":
    # Connect to Redis
    r = redis.Redis(host="localhost", port=6379, db=0)
    scope = scope_interface.ScopeInterface()
    duct_ranger = ranger.Ranger(CHIRP_DURATION, BANDWIDTH, SAMPLING_FREQUENCY)
    datalogger = duct_datalogger.DuctDatalogger()
    previously_recording = False

    while True:
        # check whether scope should be connected from redis
        desired_state = r.get("scope_desired_state").decode("utf-8")
        
        heat_map_size = r.get("heat_map_size")
        if heat_map_size is None:
            heat_map_size = 10
        else:
            heat_map_size = int(heat_map_size.decode("utf-8"))

        ranging_averaging = r.get("averaging_number")
        if ranging_averaging is None:
            ranging_averaging = 10
        else:
            ranging_averaging = int(ranging_averaging)

        distance_cutoff = r.get("distance_cutoff")
        if distance_cutoff is None:
            distance_cutoff = 900
        else:
            distance_cutoff = int(distance_cutoff)

        record_data = r.get("recording_data")
        if record_data is None:
            record_data = False
        else:
            if record_data.decode("utf-8") == "True":
                record_data = True
            else:
                record_data = False
            
        
        
        # print(f"Desired State: {desired_state}")
        # print(f"scope connected?: {scope.connected}")

        if desired_state is None and not scope.connected:
            print("no desired state")
            desired_state = "disconnect"
            r.set("scope_status", "False")
        elif desired_state == "connect" and not scope.connected:
            print("attempting to connect")
            if scope.connect_device():
                scope.configure_scope()
                scope.start_test_wavegen()
                r.set("scope_status", "True")
                print("scope connected")
            else:
                r.set("scope_status", "Unable to connect to scope")
        elif desired_state == "disconnect" and scope.connected:
            print("disconnecting from scope")
            scope.disconnect_device()
            r.set("scope_status", "False")
            
        if scope.connected:
            ch1_data, ch2_data, reading_times = scope.fetch_data()
            pulse_start_index, pulse_end_index = duct_ranger.get_first_pulse(ch1_data)
            # print("got data")

            # print(f'recording data: {record_data}')
            
            if record_data and not previously_recording:
                print("starting recording")
                datalogger.start_recording(ch1_data, ch2_data, reading_times, acquisition_time=time.time())
                previously_recording = True
            elif not record_data and previously_recording:
                print("stopping recording")
                datalogger.stop_recording()
                previously_recording = False
            elif record_data and previously_recording:
                datalogger.log_data(ch1_data, ch2_data, reading_times, acquisition_time=time.time())

            scope_measurement = {
                "ch1": ch1_data,
                "ch2": ch2_data,
                "reading_times": reading_times.tolist(),
                "pulse_start_index": pulse_start_index,
                "pulse_end_index": pulse_end_index,
            }
            # print(scope_measurement)
            r.xadd("scope_measurement", {"data": json.dumps(scope_measurement)}, maxlen=1000)      
            
            # print(f"pulse start index: {pulse_start_index}")
            # print(f"pulse end index: {pulse_end_index}")

            # take fft of chirp and get distance from fft
            chirp = ch1_data[pulse_start_index:pulse_end_index]
            square_wave = ch2_data[pulse_start_index:pulse_end_index]
            chirp_times = reading_times[pulse_start_index:pulse_end_index]

            distances, fft_freqs, magnitude = duct_ranger.get_distances(chirp)
            cutoff_mask = distances < distance_cutoff
            cutoff_distances = distances[cutoff_mask]
            cutoff_magnitudes = magnitude[cutoff_mask]
            r.xadd("distance_measurement", {"data": json.dumps({"distances": distances.tolist(), "fft_freqs": fft_freqs.tolist(), "fft_vals": magnitude.tolist(), "cutoff_magnitudes": cutoff_magnitudes.tolist(), "cutoff_distances": cutoff_distances.tolist()})}, maxlen=1000)

