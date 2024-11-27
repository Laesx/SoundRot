import datetime
import sys
import random
import time
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QListWidget, QDoubleSpinBox, QLabel, QMessageBox, QHBoxLayout, QSlider, QComboBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
import pygame

import threading
import os

class TimerManager:
    def __init__(self):
        self.timers = []

    def schedule_function(self, interval_sec, function):
        # interval_sec = interval_ms / 1000.0
        timer = threading.Timer(interval_sec, function)
        timer.start()
        self.timers.append(timer)
        return timer

    def clear_timers(self):
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()

# class TimerManager:
#     def __init__(self):
#         self.timers = []
#
#     def schedule_function(self, interval_ms, function):
#         timer = QTimer()
#         timer.setSingleShot(True)
#         timer.timeout.connect(function)
#         timer.start(msec=interval_ms)
#         self.timers.append(timer)
#         return timer
#
#     def clear_timers(self):
#         for timer in self.timers:
#             timer.stop()
#         self.timers.clear()


class AudioPlayerThread(QThread):
    """Thread for playing sounds based on random intervals."""
    signal = pyqtSignal(str)

    def __init__(self, files_with_frequencies):
        super().__init__()
        self.files_with_frequencies = files_with_frequencies
        self.running = False
        self.timer_manager = TimerManager()

    def run(self):
        self.running = True
        pygame.mixer.init()

        # Schedule initial playback for all files
        for file, frequency in self.files_with_frequencies.items():
            self.play_file(file)
            # self.schedule_next_play(file, frequency)

        while self.running:
            time.sleep(0.1)  # Keep the thread alive

    def schedule_next_play(self, file, frequency):
        # Calculate random interval based on frequency
        # interval_sec = random.expovariate(frequency / 3600.0)  # Exponential distribution
        interval_sec = random.random() * 1000 * frequency
        # interval_ms = int(interval_sec * 1000)
        print(f"Next play for {file} in {datetime.timedelta(seconds=interval_sec)} with frequency {frequency:.1f}")
        self.timer_manager.schedule_function(interval_sec, lambda: self.play_file(file))

    def play_file(self, file):
        if not self.running:
            return
        self.signal.emit(f"Playing: {file}")
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() and self.running:
            time.sleep(0.1)
        if self.running:
            # Reschedule the file for next play
            self.schedule_next_play(file, self.files_with_frequencies[file])
        self.signal.emit("Playing")

    def stop(self):
        self.running = False
        self.timer_manager.clear_timers()
        pygame.mixer.music.stop()


class RandomSoundApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sound Rot 9000")
        self.files_with_frequencies = {}
        self.player_thread = None

        # Layout and widgets
        layout = QVBoxLayout()

        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        file_controls = QHBoxLayout()
        select_files_button = QPushButton("Select Files")
        select_files_button.clicked.connect(self.select_files)
        file_controls.addWidget(select_files_button)

        remove_file_button = QPushButton("Remove Selected")
        remove_file_button.clicked.connect(self.remove_selected_file)
        file_controls.addWidget(remove_file_button)
        layout.addLayout(file_controls)

        self.frequency_slider = QSlider()
        self.frequency_slider.setOrientation(Qt.Orientation.Horizontal)
        self.frequency_slider.setRange(1, 49)
        self.frequency_slider.setValue(40)
        self.frequency_label = QLabel("Multiplier: 1.0")
        layout.addWidget(self.frequency_label)
        self.frequency_slider.valueChanged.connect(
            lambda: self.frequency_label.setText(f"Multiplier: {5 - (self.frequency_slider.value() / 10):.1f}"))
        layout.addWidget(self.frequency_slider)

        set_frequency_button = QPushButton("Set Frequency")
        set_frequency_button.clicked.connect(self.set_frequency)
        layout.addWidget(set_frequency_button)

        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label)

        start_button = QPushButton("Start")
        start_button.clicked.connect(self.start_playback)
        layout.addWidget(start_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_playback)
        layout.addWidget(stop_button)

        # save_config_button = QPushButton("Save Configuration")
        # save_config_button.clicked.connect(self.save_configuration)
        # layout.addWidget(save_config_button)
        #
        # load_config_button = QPushButton("Load Configuration")
        # load_config_button.clicked.connect(self.load_configuration)
        # layout.addWidget(load_config_button)

        # Main widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Automatically load configuration on startup
        self.load_configuration()

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Sound Files", "", "Audio Files (*.mp3 *.wav *.ogg)")
        for file in files:
            # self.add_file_to_list(file)
            if file not in self.files_with_frequencies:
                self.files_with_frequencies[file] = 1  # Default frequency
                # self.file_list.addItem(f"{file.split('/')[-1]}")
                self.add_file_to_list(file)


    def add_file_to_list(self, file):
        # self.files_with_frequencies[file] = 1
        # print(f"Added file: {file}")
        self.file_list.addItem(f"{file.split('/')[-1]}")


    # I'm ashamed of this function
    def remove_selected_file(self):
        selected_items = self.file_list.selectedItems()
        files_to_remove = []
        for item in selected_items:
            # file = item.text().split(" (")[0]
            for file in self.files_with_frequencies:
                print(f"File: {file} Item: {item.text()}")
                if file.split('/')[-1] == item.text():
                    # del self.files_with_frequencies[file]
                    files_to_remove.append(file)
                    self.file_list.takeItem(self.file_list.row(item))

        for file in files_to_remove:
            del self.files_with_frequencies[file]

    def set_frequency(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No file selected!")
            return
        frequency = 5 - (self.frequency_slider.value() / 10)
        print(f"Frequency: {frequency}")
        for item in selected_items:
            file = item.text().split(" (")[0]
            self.files_with_frequencies[file] = frequency
            item.setText(f"{file} ({frequency:.1f} multiplier)")

    def start_playback(self):
        if not self.files_with_frequencies:
            QMessageBox.warning(self, "Warning", "No files selected!")
            return
        if self.player_thread and self.player_thread.isRunning():
            QMessageBox.warning(self, "Warning", "Playback already running!")
            return

        self.player_thread = AudioPlayerThread(self.files_with_frequencies)
        self.player_thread.signal.connect(self.update_status)
        self.player_thread.start()
        self.status_label.setText("Status: Playing")

    def stop_playback(self):
        if self.player_thread:
            self.player_thread.stop()
            self.player_thread.wait()
            self.status_label.setText("Status: Stopped")

    def save_configuration(self):
        config = {"files_with_frequencies": self.files_with_frequencies}
        config_file = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_file, "w") as f:
            json.dump(config, f)
        # QMessageBox.information(self, "Success", "Configuration saved!")

    def load_configuration(self):
        config_file = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
            self.files_with_frequencies = config.get("files_with_frequencies", {})
            self.file_list.clear()
            for file, frequency in self.files_with_frequencies.items():
                self.add_file_to_list(file)
                # self.file_list.addItem(f"{file} ({frequency:.1f} plays/hour)")
            # QMessageBox.information(self, "Success", "Configuration loaded!")

    def update_status(self, message):
        self.status_label.setText(f"Status: {message}")

    def closeEvent(self, event):
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.stop()
            self.player_thread.wait()
        self.save_configuration()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = RandomSoundApp()
    main_window.show()
    sys.exit(app.exec())
