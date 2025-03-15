# Live Oscilloscope Viewer

This project is a Dash application for viewing live oscilloscope data. It includes features for connecting to a device, displaying time-domain and frequency-domain plots, and downloading data as a CSV file.

## Prerequisites

- Python (If on Windows you must have checked td/tk and IDLE checkbox during installation)
- `pip` (Python package installer)

## Setup Instructions

### 1. Clone the Repository

### 2. Create a Virtual Environment

```bash
python -m venv .radar_interface_env
```

### 3. Activate the virtual environment

On Windows:
```bash
.radar_interface_env\Scripts\activate
```

On macOS/Linux:
```bash
source .radar_interface_env/bin/activate
```

### 4. Install the Requirements

```bash
pip install -r requirements.txt
```

### 5. Launch the Dash App

```bash
python ranging_testing/data_ranging.py
```

### 6. Access the Application

Open your web browser and go to `http://127.0.0.1:8050/` to view the live oscilloscope data.