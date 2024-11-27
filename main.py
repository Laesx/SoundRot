import sys
import random
import time
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QListWidget, QSpinBox, QLabel, QMessageBox, QHBoxLayout, QSlider
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import pygame
from pygame.examples.music_drop_fade import play_file


def randommness(multiplier=1):
    return random.random() * 1000 * multiplier


class TimerManager:
    def __init__(self):
        self.timers = []

    def schedule_function(self, multiplier, function):
        interval = randommness(multiplier) * 1000  # Convert to milliseconds
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(function)
        timer.start(interval)
        self.timers.append(timer)
        return timer

    def cancel_function(self, timer):
        if timer in self.timers:
            timer.stop()
            self.timers.remove(timer)


class AudioPlayerThread(QThread):
    """Thread for playing sounds based on a frequency-driven random mechanism."""
    signal = pyqtSignal(str)
    timer_completed = pyqtSignal()

    def __init__(self, files_with_frequencies):
        super().__init__()
        self.files_with_frequencies = files_with_frequencies
        self.running = False

    def run(self):
        self.running = True
        pygame.mixer.init()
        self.timer_completed.connect(self.create_timer)
        self.create_timer()

        # while self.running:
            # for file, frequency in self.files_with_frequencies.items():
            #     # Convert frequency (plays per hour) to probability per second
            #     probability = frequency / 3600.0
            #     if random.random() < probability:  # Play the file with this probability
            #         self.signal.emit(f"Playing: {file}")
            #         pygame.mixer.music.load(file)
            #         pygame.mixer.music.play()
            #         while pygame.mixer.music.get_busy():
            #             time.sleep(0.1)
            #
            # # Short sleep to avoid overwhelming the CPU
            # time.sleep(0.1)

    def create_timer(self):
        if self.running:
            timer_manager = TimerManager()
            timer_manager.schedule_function(5, 32, play_file())

    def stop(self):
        self.running = False
        pygame.mixer.music.stop()

    def play_file(self, file):
        self.signal.emit(f"Playing: {file}")
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        self.signal.emit(f"Playing: {file}")



class RandomSoundApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random Sound Player")
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
        self.frequency_slider.setRange(0.1, 5)
        self.frequency_slider.setValue(1)
        layout.addWidget(QLabel("Set Frequency:"))
        layout.addWidget(self.frequency_slider)

        set_frequency_button = QPushButton("Set Frequency for Selected File")
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

        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_configuration)
        layout.addWidget(save_config_button)

        load_config_button = QPushButton("Load Configuration")
        load_config_button.clicked.connect(self.load_configuration)
        layout.addWidget(load_config_button)

        # Main widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Sound Files", "", "Audio Files (*.mp3 *.wav *.opus *.ogg *.flac)")
        for file in files:
            if file not in self.files_with_frequencies:
                self.files_with_frequencies[file] = 10  # Default frequency
                self.file_list.addItem(f"{file} (10 plays/hour)")

    def remove_selected_file(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            file = item.text().split(" (")[0]  # Extract file name
            del self.files_with_frequencies[file]
            self.file_list.takeItem(self.file_list.row(item))

    def set_frequency(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No file selected!")
            return
        frequency = self.frequency_slider.value()
        for item in selected_items:
            file = item.text().split(" (")[0]  # Extract file name
            self.files_with_frequencies[file] = frequency
            item.setText(f"{file} ({frequency} plays/hour)")

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
        config = {
            "files_with_frequencies": self.files_with_frequencies,
        }
        config_file, _ = QFileDialog.getSaveFileName(self, "Save Configuration", "", "JSON Files (*.json)")
        if config_file:
            with open(config_file, "w") as f:
                json.dump(config, f)
            QMessageBox.information(self, "Success", "Configuration saved!")

    def load_configuration(self):
        config_file, _ = QFileDialog.getOpenFileName(self, "Load Configuration", "", "JSON Files (*.json)")
        if config_file:
            with open(config_file, "r") as f:
                config = json.load(f)
            self.files_with_frequencies = config.get("files_with_frequencies", {})
            self.file_list.clear()
            for file, frequency in self.files_with_frequencies.items():
                self.file_list.addItem(f"{file} ({frequency} plays/hour)")
            QMessageBox.information(self, "Success", "Configuration loaded!")

    def update_status(self, message):
        self.status_label.setText(f"Status: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = RandomSoundApp()
    main_window.show()
    sys.exit(app.exec())
