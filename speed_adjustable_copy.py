import sys
import os
import shutil
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QSlider, QLabel, QProgressBar, QFileDialog,
    QMessageBox, QComboBox
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, QObject, Qt, QTimer
)

# --- Constants ---
CHUNK_SIZE = 1024 * 1024  # 1 MB chunk size for reading/writing
MAX_SPEED_MBPS = 500     # Maximum speed limit for the slider (500 MB/s)
MAX_SPEED_BPS = MAX_SPEED_MBPS * 1024 * 1024 # 524,288,000 bytes/s

class FileWorker(QObject):
    """
    Worker object running in a QThread to handle the file operation.
    It calculates the required delay to enforce the speed limit.
    """
    finished = pyqtSignal()
    progress_update = pyqtSignal(int)
    speed_update = pyqtSignal(float)
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, src_path, dest_path, operation, speed_limit_mbps):
        super().__init__()
        self.src_path = src_path
        self.dest_path = dest_path
        self.operation = operation
        self.speed_limit_mbps = speed_limit_mbps
        self._is_running = True

    def stop(self):
        """Request the thread to stop gracefully."""
        self._is_running = False

    def run(self):
        """Main file operation loop."""
        if not self._is_running:
            self.finished.emit()
            return

        try:
            self.status_message.emit(f"Starting {self.operation} operation...")
            self._execute_file_operation()
            self.status_message.emit(f"Operation complete: {self.operation.capitalize()} successful.")
        except Exception as e:
            # Handle any exceptions during the file operation
            self.error_occurred.emit(f"Error during {self.operation}: {str(e)}")
        finally:
            self.finished.emit()

    def _execute_file_operation(self):
        """Handles the throttled file copying and optional deletion (for move)."""
        file_size = os.path.getsize(self.src_path)
        bytes_copied = 0
        
        # Speed limit in bytes per second (B/s)
        # 0 MB/s is treated as full speed (MAX_SPEED_BPS) for calculation purposes, 
        # as division by zero is not allowed.
        speed_limit_bps = self.speed_limit_mbps * 1024 * 1024
        if speed_limit_bps <= 0:
            speed_limit_bps = MAX_SPEED_BPS * 2 # Set to very high value for no throttling

        start_time = time.time()
        
        with open(self.src_path, 'rb') as fsrc:
            with open(self.dest_path, 'wb') as fdst:
                while self._is_running:
                    # Time measurement for the current chunk
                    chunk_start_time = time.time()
                    
                    # Read chunk from source
                    chunk = fsrc.read(CHUNK_SIZE)
                    if not chunk:
                        break # End of file
                    
                    # Write chunk to destination
                    fdst.write(chunk)
                    
                    bytes_copied += len(chunk)
                    progress = int((bytes_copied / file_size) * 100)
                    self.progress_update.emit(progress)
                    
                    # --- Speed Throttling Logic ---
                    chunk_end_time = time.time()
                    actual_write_time = chunk_end_time - chunk_start_time
                    
                    # Calculate target time needed for this chunk based on the speed limit
                    # target_time_needed = bytes_in_chunk / speed_limit_bps
                    target_time_needed = len(chunk) / speed_limit_bps
                    
                    # Calculate delay needed
                    delay = target_time_needed - actual_write_time
                    
                    if delay > 0:
                        # Only sleep if we are faster than the speed limit
                        time.sleep(delay)
                        
                    # Calculate and emit real-time speed (since start of operation)
                    elapsed_time = time.time() - start_time
                    current_speed_bps = bytes_copied / elapsed_time if elapsed_time > 0 else 0
                    current_speed_mbps = current_speed_bps / (1024 * 1024)
                    self.speed_update.emit(current_speed_mbps)

                if not self._is_running:
                    # If stopped mid-copy, clean up the partially copied destination file
                    os.remove(self.dest_path)
                    self.status_message.emit("Operation cancelled. Partial file removed.")
                    return
        
        # If operation is 'move' and copy was successful, delete the source file
        if self.operation == "move":
            os.remove(self.src_path)
            self.status_message.emit("Source file deleted (Move operation complete).")

class FileTransferApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt File Transfer Throttler")
        self.setGeometry(100, 100, 600, 400)

        # File worker and thread
        self.worker = None
        self.worker_thread = None

        self._is_running = False

        self._setup_ui()
        self._setup_connections()
        
        # Set initial speed display
        self._update_speed_label(self.speed_slider.value())

    def _setup_ui(self):
        """Sets up all GUI elements."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Source/Destination Input ---
        file_layout = QHBoxLayout()
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Source File Path")
        self.src_btn = QPushButton("Browse Source")
        
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Destination File Path (e.g., C:/Users/Public/new_file.ext)")
        self.dest_btn = QPushButton("Browse Destination")

        file_layout.addWidget(self.src_input)
        file_layout.addWidget(self.src_btn)
        
        file_layout_2 = QHBoxLayout()
        file_layout_2.addWidget(self.dest_input)
        file_layout_2.addWidget(self.dest_btn)
        
        main_layout.addLayout(file_layout)
        main_layout.addLayout(file_layout_2)

        # --- Operation & Button ---
        control_layout = QHBoxLayout()
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItem("Copy", "copy")
        self.operation_combo.addItem("Move", "move")
        self.operation_combo.setCurrentText("Copy")
        
        self.start_btn = QPushButton("Start Operation")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; border-radius: 8px; }")
        self.stop_btn = QPushButton("Cancel Operation")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 10px; border-radius: 8px; }")

        control_layout.addWidget(self.operation_combo)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        main_layout.addLayout(control_layout)

        # --- Speed Slider ---
        speed_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed Limit:")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(0, MAX_SPEED_MBPS)
        self.speed_slider.setValue(10) # Default to 10 MB/s
        self.speed_slider.setSingleStep(1)
        
        self.speed_value_label = QLabel("10 MB/s (Real-time: N/A)")
        self.speed_value_label.setFixedWidth(200)

        speed_layout.addWidget(self.speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)
        main_layout.addLayout(speed_layout)

        # --- Progress Bar & Status ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready. Select files and set speed limit.")
        self.status_label.setStyleSheet("QLabel { padding: 5px; border: 1px solid #ccc; border-radius: 4px; }")
        main_layout.addWidget(self.status_label)
        
        # Add some spacing
        main_layout.addSpacing(20)

    def _setup_connections(self):
        """Connects signals to slots (events to functions)."""
        self.src_btn.clicked.connect(self._browse_source)
        self.dest_btn.clicked.connect(self._browse_destination)
        self.speed_slider.valueChanged.connect(self._update_speed_label)
        self.start_btn.clicked.connect(self._start_operation)
        self.stop_btn.clicked.connect(self._stop_operation)

    # --- UI Slot Functions ---

    def _browse_source(self):
        """Opens file dialog to select the source file."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Source File")
        if file_name:
            self.src_input.setText(file_name)

    def _browse_destination(self):
        """Opens file dialog to select the destination path/name."""
        # For simplicity, we just allow selecting a directory, but the user must name the file in the input.
        # A more complex version would allow selecting the destination file name directly.
        file_name, _ = QFileDialog.getSaveFileName(self, "Select Destination File Name", 
                                                    self.src_input.text())
        if file_name:
            self.dest_input.setText(file_name)
    
    def _update_speed_label(self, value):
        """Updates the label next to the slider."""
        if value == 0:
             # 0 means "unlimited" or max speed
             speed_text = "Unlimited (Max Throttling)"
        else:
             speed_text = f"{value} MB/s"
             
        # Keep the real-time speed if available, otherwise show the set limit
        current_text = self.speed_value_label.text()
        if current_text.startswith("Real-time:"):
            # Preserve the real-time info if we are mid-operation
            self.speed_value_label.setText(f"{speed_text} (Real-time: {current_text.split(': ')[1]})")
        else:
            self.speed_value_label.setText(f"{speed_text} (Real-time: N/A)")


    # --- Worker Thread Management ---

    def _start_operation(self):
        """Initiates the file operation in a new thread."""
        src = self.src_input.text()
        dest = self.dest_input.text()
        operation = self.operation_combo.currentData()
        speed_limit_mbps = self.speed_slider.value()

        # Input validation
        if not os.path.isfile(src):
            QMessageBox.warning(self, "Invalid Source", "Please select a valid source file.")
            return
        if not dest:
            QMessageBox.warning(self, "Invalid Destination", "Please provide a destination file path.")
            return

        if os.path.exists(dest):
            reply = QMessageBox.question(self, 'Overwrite File?',
                f"The destination file '{os.path.basename(dest)}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.No:
                self.status_label.setText("Operation cancelled by user (file exists).")
                return

        # Start the worker thread
        self._is_running = True
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Starting {operation}...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Disable inputs during operation
        self.src_input.setEnabled(False)
        self.dest_input.setEnabled(False)
        self.src_btn.setEnabled(False)
        self.dest_btn.setEnabled(False)
        self.operation_combo.setEnabled(False)
        self.speed_slider.setEnabled(False) # Keep speed constant during operation

        self.worker_thread = QThread()
        self.worker = FileWorker(src, dest, operation, speed_limit_mbps)
        self.worker.moveToThread(self.worker_thread)

        # Connect worker signals to main window slots
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._operation_finished)
        self.worker.progress_update.connect(self.progress_bar.setValue)
        self.worker.speed_update.connect(self._update_real_time_speed)
        self.worker.status_message.connect(self.status_label.setText)
        self.worker.error_occurred.connect(self._handle_error)

        self.worker_thread.start()

    def _stop_operation(self):
        """Stops the worker thread."""
        if self.worker and self.worker_thread.isRunning():
            self.worker.stop()
            self.status_label.setText("Cancellation requested. Waiting for thread to terminate...")
            self.stop_btn.setEnabled(False)
            
    def _operation_finished(self):
        """Cleans up after the operation is complete or cancelled."""
        self._is_running = False
        
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        # Re-enable controls
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.src_input.setEnabled(True)
        self.dest_input.setEnabled(True)
        self.src_btn.setEnabled(True)
        self.dest_btn.setEnabled(True)
        self.operation_combo.setEnabled(True)
        self.speed_slider.setEnabled(True)
        
        # Reset real-time speed display
        self._update_speed_label(self.speed_slider.value())
        
    def _update_real_time_speed(self, mbps):
        """Updates the real-time speed display."""
        # Get the current set speed text
        set_speed_text = "Unlimited (Max Throttling)"
        if self.speed_slider.value() > 0:
            set_speed_text = f"{self.speed_slider.value()} MB/s"
            
        self.speed_value_label.setText(f"{set_speed_text} (Real-time: {mbps:.2f} MB/s)")

    def _handle_error(self, message):
        """Handles errors reported by the worker thread."""
        QMessageBox.critical(self, "Operation Error", message)
        self.status_label.setText(f"Error: {message}")
        self._operation_finished() # Clean up the UI

if __name__ == "__main__":
    # Check for PyQt6 availability before running the app
    try:
        app = QApplication(sys.argv)
        window = FileTransferApp()
        window.show()
        sys.exit(app.exec())
    except ImportError:
        print("Error: PyQt6 is required to run this application.")
        print("Please install it using: pip install PyQt6")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")