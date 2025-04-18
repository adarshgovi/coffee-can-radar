import redis
import time
import json
import scope_interface
import duct_datalogger

if __name__ == "__main__":
    # Connect to Redis
    r = redis.Redis(host="localhost", port=6379, db=0)
    scope = scope_interface.ScopeInterface()
    datalogger = duct_datalogger.DuctDatalogger()
    previously_recording = False
    previously_sar_recording = False
    previously_ranging = False
    previously_doppler = False

    while True:
        # check whether scope should be connected from redis
        try:
            desired_state = r.get("scope_desired_state")
        except redis.exceptions.ConnectionError:
            print("Redis connection error, Make sure Redis is running")
            exit()
        
        if desired_state is not None:
            desired_state = desired_state.decode("utf-8") 

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
            print("Waiting for connection command from the frontend")
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
            if ((page == "ranging") and (not previously_ranging)):
                print("configuring scope for ranging")
                scope.configure_scope(trigger_level=2)
                previously_ranging = True
                previously_doppler = False
            elif ((page == "doppler") and (not previously_doppler)):
                print("configuring scope for doppler")
                scope.configure_scope(sampling_frequency=44100, amplitude_range=10)
                previously_doppler = True
                previously_ranging = False

            # print("fetching data")
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