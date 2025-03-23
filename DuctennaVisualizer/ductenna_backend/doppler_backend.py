import redis
import json
import numpy as np

SPEED_OF_LIGHT = 3e8
CENTER_FREQUENCY = 2.43e9
SAMPLING_FREQUENCY = 100000


if __name__ == "__main__":
    r = redis.Redis(host="localhost", port=6379, db=0)
    while True:
        page = r.get("current_page")
        if page is None:
            page = "home"
        else:
            page = page.decode("utf-8")
            if page == "/":
                page = "/home"
            elif page == "/doppler":
                page = "doppler"

        velocity_cutoff = r.get("velocity_cutoff")  
        if velocity_cutoff is None:
            velocity_cutoff = 50
        else:
            velocity_cutoff = float(velocity_cutoff.decode("utf-8"))
        
        heat_map_size = r.get("heat_map_size")  
        if heat_map_size is None:
            heat_map_size = 10
        else:
            heat_map_size = int(heat_map_size.decode("utf-8"))
        
        # get most recent scope measurement
        if ((scope_measurement) and (page=="doppler")):
            scope_data = r.revrange("scope_data", count=1)
            scope_measurement = scope_measurement[0][1]
            scope_measurement = json.loads(scope_measurement)
            ch1 = scope_measurement["ch1"]
            ch2 = scope_measurement["ch2"]

            # compute FFT
            fft_vals = np.abs(np.fft.fft(ch1))[:len(ch1) // 2]
            fft_freqs = np.fft.fftfreq(len(ch1), 1 / SAMPLING_FREQUENCY)[:len(ch1) // 2]
            velocities = fft_freqs * SPEED_OF_LIGHT / (2 * CENTER_FREQUENCY)

            # filter out velocities above cutoff
            mask = np.abs(velocities) < velocity_cutoff
            fft_vals_masked = fft_vals[mask]
            velocities_masked = velocities[mask]


            doppler_fft = {
                "fft_vals": fft_vals.tolist(),
                "velocities": velocities.tolist(),
                "fft_vals_cutoff": fft_vals_masked.tolist(),
                "velocities_cutoff": velocities_masked.tolist()
            }
            r.xadd("doppler_fft", {"data": json.dumps(doppler_fft)}, maxlen=1000)

            # compute heat map
            # retrieve last velocities, up to heat map size
            # cutoff the velocities to the current cutoff
            # compute the heat map

            velocities = r.revrange("doppler_fft", count=heat_map_size)
            velocities = [json.loads(v[1])["velocities_cutoff"] for v in velocities]
            velocities = np.array(velocities)
            velocities = np.array([v[:len(velocities[0])] for v in velocities])

            heat_map = np.abs(velocities)
            r.xadd("doppler_heat_map", {"data": json.dumps(heat_map.tolist())}, maxlen=1000)