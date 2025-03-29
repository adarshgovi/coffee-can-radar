# **Ductenna Visualizer**

## **Overview**
The Ductenna Visualizer is a system designed to process and visualize radar data for ranging and Doppler velocity measurements. It consists of a backend for data acquisition and processing, and a frontend for real-time visualization using Dash.

---

## **Features**
- **Ranging Dashboard**: Displays raw signals, FFT plots, and heatmaps for distance measurements.
- **Doppler Dashboard**: Displays raw signals, FFT plots, and heatmaps for velocity measurements.
- **Real-Time Data Processing**: Processes radar data in real-time using Redis for communication between the backend and frontend.
- **User Interaction**: Allows users to configure parameters such as averaging, heatmap size, and cutoff values.

---

## **Installation Requirements**

### **1. Install Python and Virtual Environment**
- Ensure you have Python 3.8 or later installed.
- Create a virtual environment in the DuctennaVisualizer folder:
  ```bash
  cd {ProjectDirectory}/DuctennaVisualizer
  python3 -m venv .ductenna_venv

- Activate the virual environment
    - On Mac:

    ```bash
    source .ductenna_venv/bin/activate
    ```

    - On Windows
    ```bash
    .ductenna_venv\Scripts\active
    ```
### 2. Install required Python packages

- Install the required Python pacakges in `requirements.txt`

```bash
pip install requirements.txt
```
### 3. Install Docker
- Install Docker from Docker's official website.
- Docker is used to run a Redis container for inter-process communication.
- Ensure Docker is running before starting the system.

4. Install Docker Compose
- Docker Compose is required to manage the Redis container. It is typically included with Docker Desktop. 
- Verify installation:
```bash
docker-compose --version
```
<!-- section break -->

## Usage Instructions
### 1. Start the Entire System
Run the start_system.sh script to start the backend, frontend, and Redis services:

This script performs the following steps:

1. Activates the virtual environment.
2. Starts a Redis container using Docker Compose.
Launches the backend processes (ductenna_backend.py and doppler_backend.py).
3/ Launches the Dash frontend (visualizer.py).
### 2. Access the Dash App
- Open your browser and navigate to http://127.0.0.1:8050 to access the visualization dashboard.
### 3. Stop the System
- Press `Ctrl+C` in the terminal to stop the system.
- The script will automatically clean up by stopping the Redis container and deactivating the virtual environment.


## Running Components Separately

1. Start Redis
Start the Redis container using Docker Compose:
```bash
docker-compose up -d
```
2. Run the Backend
- Ranging Backend:
```bash
python ductenna_backend/ductenna_backend.py
```
- Doppler Backend:
```bash
python ductenna_backend/doppler_backend.py
```
3. Run the Frontend
Start the Dash app for visualization:
```bash
python ductenna_frontend/visualizer.py
```

## Project Structure
```
DuctennaVisualizer/
├── ductenna_backend/
│   ├── ductenna_backend.py       # Backend for ranging data processing
│   ├── doppler_backend.py        # Backend for Doppler data processing
│   ├── ranger.py                 # Ranging calculations
│   ├── duct_datalogger.py        # Data logging functionality
├── ductenna_frontend/
│   ├── visualizer.py             # Dash app for visualization
├── docker-compose.yml            # Docker Compose configuration for Redis
├── requirements.txt              # Python dependencies
├── start_system.sh               # Script to start the system
```

## Key Components
1. Backend
Key Components
1. Backend
- ductenna_backend.py:
  - Handles ranging data acquisition and processing.
  - Computes FFT and generates heatmaps for distance measurements.
  - Publishes processed data to Redis streams.

- doppler_backend.py:
  - Handles Doppler data acquisition and processing.
  - Computes FFT and generates heatmaps for velocity measurements.
Publishes processed data to Redis streams.
2. Frontend
visualizer.py:
Dash app for real-time visualization.
Provides two dashboards:
Ranging Dashboard: Displays raw signals, FFT plots, and distance heatmaps.
Doppler Dashboard: Displays raw signals, FFT plots, and velocity heatmaps.
Allows users to configure parameters and control the system.