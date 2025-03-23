import csv
from datetime import datetime
import os

class DuctDatalogger:
    def __init__(self):
        self.csv_writer = None
        self.sar_writer = None
        self.sar_file = None
        self.csv_file = None
        self.recording = False
        self.sar_recording = False

    def start_recording(self, ch1_data, ch2_data, reading_times, acquisition_time):
        # Create a timestamped filename for the recording
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_filename = f"recordings/recording_{timestamp}.csv"
        print(f"Recording to {csv_filename}")

        # Open the CSV file and write the header
        self.csv_file = open(csv_filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.csv_writer.writerow(["Acquisition Time", "Reading Time", "Channel 1", "Channel 2"])

        # Write the initial batch of data
        self.log_data(ch1_data, ch2_data, reading_times, acquisition_time)
        self.recording = True

    def stop_recording(self):
        if self.csv_file:
            self.csv_file.close()
        self.recording = False

    def log_data(self, ch1_data, ch2_data, reading_times, acquisition_time):
        # Write data rows to the CSV file
        for i in range(len(ch1_data)):
            self.csv_writer.writerow([acquisition_time, reading_times[i], ch1_data[i], ch2_data[i]])

    def sar_record(self, ch1_data, ch2_data, reading_times, acquisition_time, position):
        csv_filename = f"recordings/recording_{position}.csv"
        print(f"Recording to {csv_filename}")

        # Open the CSV file and write the header
        self.sar_file = open(csv_filename, mode='w', newline='')
        self.sar_writer = csv.writer(self.csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.sar_writer.writerow(["Acquisition Time", "Reading Time", "Channel 1", "Channel 2"])

        # Write the initial batch of data
        self.log_data(ch1_data, ch2_data, reading_times, acquisition_time)
        self.sar_recording = True
    
    def sar_log_data(self, ch1_data, ch2_data, reading_times, acquisition_time):
        # Write data rows to the CSV file
        for i in range(len(ch1_data)):
            self.sar_writer.writerow([acquisition_time, reading_times[i], ch1_data[i], ch2_data[i]])

    def stop_sar_recording(self):
        if self.sar_file:
            self.sar_file.close()
        self.sar_recording = False