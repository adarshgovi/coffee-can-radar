import redis
import json
import numpy as np
import ranger

# constants 
SPEED_OF_LIGHT = 3e8
BANDWIDTH = 250e6
CHIRP_DURATION = 0.02
SAMPLING_FREQUENCY = 100000

if __name__ == "__main__":
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    duct_ranger = ranger.Ranger(CHIRP_DURATION, BANDWIDTH, SAMPLING_FREQUENCY)

    while True:
        page = r.get("current_page")
        if page is None:
            page = "home"
        else:
            if page == "/":
                page = "ranging"
            elif page == "/doppler":
                page = "doppler"
        
        distances = r.get("distance_cutoff")
        if distances is None:
            distance_cutoff = 900
        else:
            distance_cutoff = int(distances)
        
        heat_map_size = r.get("heat_map_size")
        if heat_map_size is None:
            heat_map_size = 10
        else:
            heat_map_size = int(heat_map_size)

        # take fft of chirp and get distance from fft
        if page == "ranging":
            scope_measurement = r.xrevrange("scope_measurement", count=1)
            if scope_measurement:
                # read data from redis
                scope_measurement = scope_measurement[0][1]
                scope_measurement = json.loads(scope_measurement['data'])
                ch1_data = np.array(scope_measurement['ch1'])
                ch2_data = np.array(scope_measurement['ch2'])
                reading_times = np.array(scope_measurement['reading_times'])
                
            pulse_start_index, pulse_end_index = duct_ranger.get_first_pulse(ch1_data)
            pulse_indices = {"pulse_start_index": pulse_start_index, "pulse_end_index": pulse_end_index}
            r.xadd("pulse_indices", {"data": json.dumps(pulse_indices)}, maxlen=1000)
            # print(f"pulse start index: {pulse_start_index}")
            # print(f"pulse end index: {pulse_end_index}")
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
                data = json.loads(entry_data["data"])
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