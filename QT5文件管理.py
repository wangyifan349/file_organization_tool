import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox, QComboBox
)
from PyQt5.QtCore import pyqtSignal, QObject, QThread

# Define supported video and image file formats
VIDEO_FORMATS = ['.mp4', '.avi', '.mkv', '.mov']
IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

class FileOperationWorker(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, media_files, destination_directory, action):
        super().__init__()
        self.media_files = media_files
        self.destination_directory = destination_directory
        self.action = action

    def run(self):
        for file_path in self.media_files:
            base_name = os.path.basename(file_path)
            destination_file_path = os.path.join(self.destination_directory, base_name)

            # Avoid overwriting files by checking for existing destination
            if os.path.exists(destination_file_path):
                base, extension = os.path.splitext(base_name)
                counter = 1
                while os.path.exists(destination_file_path):
                    new_file_name = f"{base}_{counter}{extension}"
                    destination_file_path = os.path.join(self.destination_directory, new_file_name)
                    counter += 1

            try:
                if self.action == 'move':
                    shutil.move(file_path, destination_file_path)
                    self.progress.emit(f"Moved: {file_path}")
                else:
                    shutil.copy2(file_path, destination_file_path)
                    self.progress.emit(f"Copied: {file_path}")
            except Exception as e:
                self.progress.emit(f"Error with {file_path}: {str(e)}")

        self.finished.emit("File operation completed successfully!")

class MediaFileManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Media File Manager")
        self.setGeometry(100, 100, 450, 150)

        layout = QVBoxLayout()

        self.status_label = QLabel("Select the root directory to search for media files.")
        layout.addWidget(self.status_label)

        select_root_button = QPushButton("Select Root Directory")
        select_root_button.clicked.connect(self.select_root_directory)
        layout.addWidget(select_root_button)

        self.action_combo = QComboBox()
        self.action_combo.addItem("Copy")
        self.action_combo.addItem("Move")
        layout.addWidget(self.action_combo)

        self.setLayout(layout)

        # Set stylesheet for the application
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QComboBox {
                border: 1px solid #aaa;
                border-radius: 5px;
                padding: 5px;
            }
        """)

    def select_root_directory(self):
        root_directory = QFileDialog.getExistingDirectory(self, "Select Root Directory")
        if root_directory:
            media_files = self.find_media_files(root_directory)
            if not media_files:
                QMessageBox.information(self, "No Media Files", "No media files found in the selected directory.")
                return

            self.status_label.setText(f"Found {len(media_files)} media files")
            proceed = QMessageBox.question(self, "Proceed",
                                           f"Found {len(media_files)} media files. Do you want to proceed?",
                                           QMessageBox.Yes | QMessageBox.No)

            if proceed == QMessageBox.Yes:
                destination_directory = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
                if destination_directory:
                    self.start_worker(media_files, destination_directory)

    def find_media_files(self, root_directory):
        media_files = []
        for directory_path, _, file_names in os.walk(root_directory):
            for file_name in file_names:
                _, file_extension = os.path.splitext(file_name)
                if file_extension.lower() in VIDEO_FORMATS or file_extension.lower() in IMAGE_FORMATS:
                    file_path = os.path.join(directory_path, file_name)
                    media_files.append(file_path)
        return media_files

    def start_worker(self, media_files, destination_directory):
        action = self.action_combo.currentText().lower()

        # Set up worker and thread
        self.thread = QThread()
        self.worker = FileOperationWorker(media_files, destination_directory, action)
        self.worker.moveToThread(self.thread)

        # Connect signals and slots
        self.worker.finished.connect(self.on_finished)
        self.worker.progress.connect(self.update_status)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_status(self, message):
        self.status_label.setText(message)

    def on_finished(self, message):
        QMessageBox.information(self, "Operation Completed", message)

def main():
    app = QApplication(sys.argv)
    ex = MediaFileManager()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
