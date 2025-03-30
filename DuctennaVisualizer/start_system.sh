#!/bin/bash
# Step 1: Activate Virtual Environment
echo "Activating virtual environment..."
source /Users/adarshgovindan/School/Capstone/CCRadarSim/DuctennaVisualizer/ductenna_backend/.ductenna_env/bin/activate  # Change to match your venv path

# Step 2: Start Redis in Docker (if not already running)
echo "Starting Redis container..."
docker-compose up -d

# Wait for Redis to be ready
sleep 2  # Adjust based on startup time

# Step 3: Start the Sensor Logger (Backend)
echo "Starting Scope Readings and Ranging..."
python ductenna_backend/ductenna_backend.py &

# Step 4: Start the Dash App (Frontend)
echo "Starting Visualization Dashboard..."
python ductenna_frontend/visualizer.py &

echo "Starting Range Processing backend..."
python ductenna_backend/range_backend.py &

echo "Starting Doppler Processing backend..."
python ductenna_backend/doppler_backend.py & 

# Step 5: Wait for user to terminate
echo "System started! Press Ctrl+C to stop..."
wait  # Keeps script running until manually stopped

# Step 6: Cleanup (Stop Services)
echo "Stopping services..."
docker-compose down  # Stops Redis
kill $(jobs -p)  # Stops Python scripts
deactivate  # Exit virtual environment
echo "System stopped!"
