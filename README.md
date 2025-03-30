# Coffee Can Radar Project

An experimental radar system inspired by the MIT Coffee Can Radar, with enhanced features for real-time data visualization, signal processing, and antenna performance analysis. This repository hosts all code, simulations, and tools used in the design, implementation, and improvement of the radar system.

## 📂 Repository Structure

```
CCRadarSim/
│
├── DuctennaVisualizer/        # Real-time visualization & signal processing tools
├── antenna_analysis/          # Antenna simulations
├── README.md                  # This file
└── requirements.txt           # Python dependencies
```

## 🚀 Project Overview

This project aims to build and improve upon the MIT Coffee Can Radar system. Our key contributions include:

- 🚐 **Real-time signal processing** via Python Dash interface  
- 📡 **Antenna analysis and optimization** using simulation tools and empirical testing  
- 📈 **Tools for range measurement, Doppler shift analysis, and Synthetic Aperture Radar (SAR)**

The system is being developed as part of an undergraduate capstone project, with a goal of creating a relatively low-cost, portable radar system for educational and research purposes.

## 🔍 DuctennaVisualizer

This module provides:

- Real-time range and Doppler visualization  
- Dash-based web interface for live radar data streaming  
- Signal processing features including:
  - Fast Fourier Transform (FFT)
  - SAR data collection (experimental)

**Example features**:
- Real-time data streaming from radar front-end
- Range-Doppler heatmap visualization
- Adjustable visualization windows and parameters 
- Data recording

## 📡 antenna_analysis

This folder contains:

- MATLAB and Python scripts for antenna design and analysis   

We tested and tuned the Coffee Can antenna for improved S11 response and forward gain. To be documented in detail in the future.


## 🛠️ Installation & Setup

> Ensure you have Python 3.8+, pip, docker and waveforms SDK installed.


```bash
git clone https://github.com/yourusername/coffee-can-radar.git
cd CCRadarSim
pip install -r requirements.txt
```

You’ll also need a working radar front-end (e.g., MIT I/Q board) and a USB-compatible ADC (such as the Digilent AD2 in our case).

## 📊 Usage

### Launching Real-Time Visualizer:

```bash
cd DuctennaVisualizer
bash start_system.sh
```

Visit `http://localhost:8050` (this can be found in the terminal output) in your browser to view the live dashboard.

## 🧪 Testing & Simulation

To review antenna designs:

```bash
cd antenna_analysis
# View MATLAB results or open .m files with appropriate tools
```

## 🔬 Features in Progress

- SAR processing in Python
- Improved Range and Doppler algorithms
- Fine-tuning of antenna designs

## 👨‍💻 Team

This project is developed by undergraduate researchers at UBC as part of the final year capstone project. Special thanks to our faculty advisors and the open-source radar community.

**Contributors:**
- Adarsh Govindan  
- Gavin Pringle  
- Farhan Ishraq  
- Yousif El-Wishahy

## 🙌 Acknowledgements

- [MIT Coffee Can Radar](https://ocw.mit.edu/courses/res-ll-003-build-a-small-radar-system-capable-of-sensing-range-doppler-and-synthetic-aperture-radar-imaging-january-iap-2011/)  
- UBC Engineering Physics (ENPH 479) 
- Nick Peereboom
- UBC Department of Physics & Astronomy