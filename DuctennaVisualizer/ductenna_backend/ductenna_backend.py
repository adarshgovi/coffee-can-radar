import redis
import time
import json
import numpy as np
import scope_interface
import ranger
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

    while True:
        # check whether scope should be connected from redis
        desired_state = r.get("scope_desired_state").decode("utf-8")
        print(f"Desired State: {desired_state}")
        print(f"scope connected?: {scope.connected}")

        if desired_state is None and not scope.connected:
            print("no desired state")
            desired_state = "disconnect"
            r.set("scope_status", "False")
        elif desired_state == "connect" and not scope.connected:
            print("attempting to connect")
            if scope.connect_device():
                scope.configure_scope()
                r.set("scope_status", "True")
                print("scope connected")
            else:
                r.set("scope_status", "Unable to connect to scope")
        elif desired_state == "disconnect" and scope.connected:
            print("disconnecting from scope")
            scope.disconnect_device()
            r.set("scope_status", "False")
            
        if scope.connected:
            ch1_data, ch2_data, time = scope.fetch_data()
            pulse_start_index, pulse_end_index = duct_ranger.get_first_pulse(ch1_data, ch2_data)
            print("got data")
            # if redis says we should be recording, and we're not already recording, start recording
            # if redis says we should be recording, and we're already recording, continue recording
            # if redis says we shouldn't be recording, and we're recording, stop recording
            # if redis says we shouldn't be recording, and we're not recording, do nothing

            print(f"pulse start index: {pulse_start_index}")
            print(f"pulse end index: {pulse_end_index}")

            # take fft of chirp and get distance from fft
            chirp = ch1_data[pulse_start_index:pulse_end_index]
            # print(chirp)
            square_wave = ch2_data[pulse_start_index:pulse_end_index]
            time = time[pulse_start_index:pulse_end_index]

            scope_measurement = {
                "chirp": chirp,
                "square_wave": square_wave
            }
            print(scope_measurement)
            r.xadd("scope_measurement", {"data": json.dumps(scope_measurement)}, maxlen=1000)      
            
            # fft_vals, fft_freqs = np.fft.fft(chirp), np.fft.fftfreq(len(chirp), 1/scope.sampling_frequency)
            # mask = (fft_freqs < 5000)
            # fft_freqs, fft_vals = fft_freqs[mask], fft_vals[mask]
            # peak_index = np.argmax(fft_vals)
            # peak_freq = fft_freqs[peak_index] if len(fft_freqs) > 0 else 0
            # peak_distance = duct_ranger.get_distance(peak_freq)

            # Store data in Redis

        # sensor_value = np.random.random()
        # timestamp = time.time()

        # # Store data in Redis
        # r.xadd("sensor_stream", {'timestamp': timestamp, 'value': sensor_value})
        
        # print(f"Sent data: {timestamp}, {sensor_value}")
        # time.sleep(0.1)  # Adjust based on real sensor data rate
