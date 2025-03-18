import redis
import time
import json
import numpy as np

# Connect to Redis (Docker is running it on localhost:6379)
r = redis.Redis(host="localhost", port=6379, db=0)

while True:
    # Simulate sensor data
    sensor_value = np.random.random()
    timestamp = time.time()

    # Store data in Redis
    r.xadd("sensor_stream", {'timestamp': timestamp, 'value': sensor_value})
    
    print(f"Sent data: {timestamp}, {sensor_value}")
    time.sleep(0.1)  # Adjust based on real sensor data rate
