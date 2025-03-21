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
1. Start the Entire System
Run the start_system.sh script to start the backend, frontend, and Redis services:

This script performs the following steps:

Activates the virtual environment.
Starts a Redis container using Docker Compose.
Launches the backend processes (ductenna_backend.py and doppler_backend.py).
Launches the Dash frontend (visualizer.py).
2. Access the Dash App
Open your browser and navigate to http://127.0.0.1:8050 to access the visualization dashboard.
3. Stop the System
Press Ctrl+C in the terminal to stop the system.
The script will automatically clean up by stopping the Redis container and deactivating the virtual environment.