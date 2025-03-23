import csv
from datetime import datetime
import os

class DuctDatalogger:
    def __init__(self):
        self.csv_writer = None
        self.csv_file = None
        self.recording = False

    def start_recording(self, ch1_data, ch2_data, reading_times, acquisition_time):
        # Create a timestamped filename for the recording
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if not os.path.exists("recordings"):
            os.makedirs("recordings")
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