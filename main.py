import sys
import random
import time
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QListWidget, QSpinBox, QLabel, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
import pygame


class AudioPlayerThread(QThread):
    """Thread for playing sounds randomly with a delay."""
    signal = pyqtSignal(str)

    def __init__(self, files, frequency):
        super().__init__()
        self.files = files
        self.frequency = frequency
        self.running = False

    def run(self):
        self.running = True
        pygame.mixer.init()
        while self.running and self.files:
            sound_file = random.choice(self.files)
            self.signal.emit(f"Playing: {sound_file}")
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            time.sleep(self.frequency)

    def stop(self):
        self.running = False
        pygame.mixer.music.stop()


class RandomSoundApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random Sound Player")
        self.files = []
        self.player_thread = None

        # Layout and widgets
        layout = QVBoxLayout()

        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        select_files_button = QPushButton("Select Files")
        select_files_button.clicked.connect(self.select_files)
        layout.addWidget(select_files_button)

        self.frequency_spinbox = QSpinBox()
        self.frequency_spinbox.setRange(1, 3600)
        self.frequency_spinbox.setValue(10)
        layout.addWidget(QLabel("Frequency (seconds):"))
        layout.addWidget(self.frequency_spinbox)

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
        files, _ = QFileDialog.getOpenFileNames(self, "Select Sound Files", "", "Audio Files (*.mp3 *.wav)")
        if files:
            self.files.extend(files)
            self.file_list.addItems(files)

    def start_playback(self):
        if not self.files:
            QMessageBox.warning(self, "Warning", "No files selected!")
            return

        if self.player_thread and self.player_thread.isRunning():
            QMessageBox.warning(self, "Warning", "Playback already running!")
            return

        frequency = self.frequency_spinbox.value()
        self.player_thread = AudioPlayerThread(self.files, frequency)
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
            "files": self.files,
            "frequency": self.frequency_spinbox.value(),
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
            self.files = config.get("files", [])
            self.file_list.clear()
            self.file_list.addItems(self.files)
            self.frequency_spinbox.setValue(config.get("frequency", 10))
            QMessageBox.information(self, "Success", "Configuration loaded!")

    def update_status(self, message):
        self.status_label.setText(f"Status: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = RandomSoundApp()
    main_window.show()
    sys.exit(app.exec())
