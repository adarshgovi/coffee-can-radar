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
    previously_ranging = False
    previously_sar_recording = False

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
        
        position = r.get("position_label")
        if position is None:
            position = None
        else:
            position = int(position)

        record_data = r.get("recording_data")
        if record_data is None:
            record_data = False
        else:
            if record_data.decode("utf-8") == "True":
                record_data = True
            else:
                record_data = False
        
        page = r.get("current_page")
        if page is None:
            page = "home"
        else:
            page = page.decode("utf-8")
            if page =="/":
                page = "ranging"
            elif page =="/doppler":
                page = "doppler"

        if desired_state is None and not scope.connected:
            print("no desired state")
            desired_state = "disconnect"
            r.set("scope_status", "False")
        elif desired_state == "connect" and not scope.connected:
            print("attempting to connect")
            if scope.connect_device():
                scope.configure_scope()
                # scope.start_test_wavegen()
                r.set("scope_status", "True")
                print("scope connected")
            else:
                r.set("scope_status", "Unable to connect to scope")
        elif desired_state == "disconnect" and scope.connected:
            print("disconnecting from scope")
            scope.disconnect_device()
            r.set("scope_status", "False")
            
        if scope.connected:
            if ((page == "ranging") and (not previously_ranging)):
                print("configuring scope for ranging")
                previously_ranging = True
                previously_doppler = False
            elif ((page == "doppler") and (not previously_doppler)):
                print("configuring scope for doppler")
                previously_doppler = True
                previously_ranging = False

            ch1_data, ch2_data, reading_times = scope.fetch_data()
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
            }
            # print(scope_measurement)
            r.xadd("scope_measurement", {"data": json.dumps(scope_measurement)}, maxlen=1000)

            if position is not None:
                ch1_data, ch2_data, reading_times = scope.fetch_data()
                if record_data and not previously_sar_recording:
                    print("starting SAR recording")
                    datalogger.sar_record(ch1_data, ch2_data, reading_times, acquisition_time=time.time(), position=position)
                    previously_sar_recording = True
                elif not record_data and previously_sar_recording:
                    print("stopping SAR recording")
                    datalogger.stop_sar_recording()
                    previously_sar_recording = False
                elif record_data and previously_sar_recording:
                    datalogger.sar_log_data(ch1_data, ch2_data, reading_times, acquisition_time=time.time())
            
            # print(f"pulse start index: {pulse_start_index}")
            # print(f"pulse end index: {pulse_end_index}")

            # take fft of chirp and get distance from fft
            if page == "ranging":
                pulse_start_index, pulse_end_index = duct_ranger.get_first_pulse(ch1_data)
                pulse_indices = {"pulse_start_index": pulse_start_index, "pulse_end_index": pulse_end_index}
                r.xadd("pulse_indices", {"data": json.dumps(pulse_indices)}, maxlen=1000)
                print(f"pulse start index: {pulse_start_index}")
                print(f"pulse end index: {pulse_end_index}")
                square_wave = ch1_data[pulse_start_index:pulse_end_index]
                chirp = ch2_data[pulse_start_index:pulse_end_index]
                chirp_times = reading_times[pulse_start_index:pulse_end_index]

                distances, fft_freqs, magnitude = duct_ranger.get_distances(chirp)
                cutoff_mask = distances < distance_cutoff
                cutoff_distances = distances[cutoff_mask]
                cutoff_magnitudes = magnitude[cutoff_mask]
                r.xadd("distance_measurement", {"data": json.dumps({"distances": distances.tolist(), "fft_freqs": fft_freqs.tolist(), "fft_vals": magnitude.tolist(), "cutoff_magnitudes": cutoff_magnitudes.tolist(), "cutoff_distances": cutoff_distances.tolist()})}, maxlen=1000)

                recent_entries = r.xrevrange("distance_measurement", count=heat_map_size)
                heatmap = []
                for entry_id, entry_data in reversed(recent_entries):  # Reverse to maintain chronological order
                    data = json.loads(entry_data[b"data"])
                    distances = np.array(data["distances"])
                    magnitudes = np.array(data["fft_vals"])
                    # Apply the distance cutoff mask dynamically
                    cutoff_mask = distances < distance_cutoff
                    cropped_magnitudes = magnitudes[cutoff_mask]

                    heatmap.append(cropped_magnitudes)
                
                heatmap = np.array(heatmap)
                # Push the heatmap data to Redis
                r.xadd(
                    "heatmap_data",
                    {
                        "data": json.dumps({"heatmap": heatmap.tolist()})
                    },
                    maxlen=100
                )
