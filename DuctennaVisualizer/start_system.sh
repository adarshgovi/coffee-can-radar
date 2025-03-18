#!/bin/bash
# Step 1: Start Redis in Docker (if not already running)
echo "Starting Redis container..."
docker-compose up -d

# Wait for Redis to be ready
sleep 2  # Adjust based on startup speed

# Step 2: Start the Sensor Logger (Backend)
echo "Starting Backend..."
python sensor_logger.py &

# 🚀 Step 3: Start the Dash App (Frontend)
echo "Starting Frontend..."
python dash_app.py &

# 🚀 Step 4: Wait for user to terminate
echo "System started! Press Ctrl+C to stop..."
wait  # Keeps script running until manually stopped

# 🚀 Step 5: Cleanup (Stop Background Processes)
echo "Stopping services..."
docker-compose down  # Stops Redis
kill $(jobs -p)  # Stops Python scripts
echo "System stopped!"
