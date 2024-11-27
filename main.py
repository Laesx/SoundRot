import sys
import random
import time
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QListWidget, QDoubleSpinBox, QLabel, QMessageBox, QHBoxLayout, QSlider
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
import pygame


class TimerManager:
    def __init__(self):
        self.timers = []

    def schedule_function(self, interval_ms, function):
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(function)
        timer.start(interval_ms)
        self.timers.append(timer)
        return timer

    def clear_timers(self):
        for timer in self.timers:
            timer.stop()
        self.timers.clear()


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
            self.schedule_next_play(file, frequency)

        while self.running:
            time.sleep(0.1)  # Keep the thread alive

    def schedule_next_play(self, file, frequency):
        # Calculate random interval based on frequency (plays/hour)
        interval_sec = random.expovariate(frequency / 3600.0)  # Exponential distribution
        interval_ms = int(interval_sec * 1000)
        print(f"Next play for {file} in {interval_sec:.1f} seconds")
        self.timer_manager.schedule_function(interval_ms, lambda: self.play_file(file))

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

    def stop(self):
        self.running = False
        self.timer_manager.clear_timers()
        pygame.mixer.music.stop()


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
        self.frequency_slider.setOrientation(Qt.Orientation.Horizontal)
        self.frequency_slider.setRange(1, 5)
        self.frequency_slider.setValue(1)
        layout.addWidget(QLabel("Set Frequency:"))
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
        files, _ = QFileDialog.getOpenFileNames(self, "Select Sound Files", "", "Audio Files (*.mp3 *.wav *.ogg)")
        for file in files:
            if file not in self.files_with_frequencies:
                self.files_with_frequencies[file] = 10.0  # Default frequency
                self.file_list.addItem(f"{file} (10.0 plays/hour)")

    def remove_selected_file(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            file = item.text().split(" (")[0]
            del self.files_with_frequencies[file]
            self.file_list.takeItem(self.file_list.row(item))

    def set_frequency(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No file selected!")
            return
        frequency = self.frequency_spinbox.value()
        for item in selected_items:
            file = item.text().split(" (")[0]
            self.files_with_frequencies[file] = frequency
            item.setText(f"{file} ({frequency:.1f} plays/hour)")

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
                self.file_list.addItem(f"{file} ({frequency:.1f} plays/hour)")
            QMessageBox.information(self, "Success", "Configuration loaded!")

    def update_status(self, message):
        self.status_label.setText(f"Status: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = RandomSoundApp()
    main_window.show()
    sys.exit(app.exec())
