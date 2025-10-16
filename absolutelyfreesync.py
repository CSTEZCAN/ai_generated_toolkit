import sys
import os
import shutil
import hashlib
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QLabel, QListWidget,
    QMessageBox, QFileDialog, QProgressBar, QDialog, QFormLayout
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QMutex

# =====================================================================
# Worker Thread for File Operations
# =====================================================================

class FileOperationWorker(QThread):
    """Worker thread to perform file operations without freezing the UI."""

    # Signals for communication with the main thread
    operation_progress = pyqtSignal(int, str, str) # task_index, filename, message
    operation_finished = pyqtSignal(int, bool, str) # task_index, success, message
    overall_progress = pyqtSignal(int) # percentage of current task completed

    def __init__(self, task_list):
        super().__init__()
        self.task_list = task_list
        self._is_running = True
        self.mutex = QMutex()

    def stop(self):
        """Safely stop the thread."""
        self.mutex.lock()
        self._is_running = False
        self.mutex.unlock()

    def run(self):
        """Main execution function of the thread."""
        for i, task in enumerate(self.task_list):
            self.mutex.lock()
            if not self._is_running:
                self.mutex.unlock()
                break # Stop if requested
            self.mutex.unlock()

            source = task['source']
            destination = task['destination']
            mode = task['mode']
            
            # Reset progress for the new task
            self.overall_progress.emit(0)
            
            # --- Perform Operation ---
            try:
                if mode in ['verify_and_delete', 'copy']:
                    self._process_directory(i, source, destination, mode)
                else:
                    self.operation_finished.emit(i, False, f"Unknown mode: {mode}")

            except Exception as e:
                self.operation_finished.emit(i, False, f"Critical Error: {e}")
        
        # Final overall progress to show completion
        self.overall_progress.emit(100)

    def _process_directory(self, task_index, src_dir, dst_dir, mode):
        """Processes files within the source directory."""
        
        if not os.path.exists(src_dir):
            self.operation_finished.emit(task_index, False, f"Source directory not found: {src_dir}")
            return
        
        os.makedirs(dst_dir, exist_ok=True)
        
        all_files = [os.path.join(dp, f) for dp, dn, fn in os.walk(src_dir) for f in fn]
        total_files = len(all_files)
        
        if total_files == 0:
            self.operation_finished.emit(task_index, True, f"Source directory is empty. Operation successful.")
            return

        for file_idx, src_filepath in enumerate(all_files):
            self.mutex.lock()
            if not self._is_running:
                self.mutex.unlock()
                return # Stop processing
            self.mutex.unlock()
            
            rel_path = os.path.relpath(src_filepath, src_dir)
            dst_filepath = os.path.join(dst_dir, rel_path)
            os.makedirs(os.path.dirname(dst_filepath), exist_ok=True)
            filename = os.path.basename(src_filepath)

            # 1. Copy/Move Operation
            self.operation_progress.emit(task_index, filename, "Copying...")
            shutil.copy2(src_filepath, dst_filepath) # copy2 preserves metadata

            # 2. MD5 Verification
            self.operation_progress.emit(task_index, filename, "Verifying MD5...")
            src_md5 = self._calculate_md5(src_filepath)
            dst_md5 = self._calculate_md5(dst_filepath)

            if src_md5 != dst_md5:
                self.operation_finished.emit(task_index, False, f"MD5 Mismatch for {filename}. Copy failed.")
                return # Stop task on verification failure

            # 3. Delete from Source (if mode is 'verify_and_delete' - secure move)
            if mode == 'verify_and_delete':
                self.operation_progress.emit(task_index, filename, "Deleting Source...")
                os.remove(src_filepath)
                # Note: Directory cleanup (removing empty source folders) is left out for simplicity
                # but could be added here.
            
            # Update overall progress for the current task
            progress_percent = int((file_idx + 1) / total_files * 100)
            self.overall_progress.emit(progress_percent)

        self.operation_finished.emit(task_index, True, f"Operation **{mode}** successful.")

    def _calculate_md5(self, filepath, blocksize=65536):
        """Calculates MD5 hash for a file."""
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as afile:
                buf = afile.read(blocksize)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = afile.read(blocksize)
            return hasher.hexdigest()
        except Exception:
            # Return an invalid hash if the file can't be opened
            return "ERROR_HASH"

# =====================================================================
# Task Setup Dialog
# =====================================================================

class TaskSetupDialog(QDialog):
    """Dialog to add a new file operation task."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")
        self.setGeometry(100, 100, 500, 200)

        layout = QFormLayout(self)
        
        self.source_line = QLineEdit()
        self.source_btn = QPushButton("Browse Source Folder")
        self.source_btn.clicked.connect(lambda: self._browse_folder(self.source_line))
        
        self.dest_line = QLineEdit()
        self.dest_btn = QPushButton("Browse Destination Folder")
        self.dest_btn.clicked.connect(lambda: self._browse_folder(self.dest_line))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Verify and Delete (Secure Move)", "verify_and_delete")
        self.mode_combo.addItem("Copy (Clone)", "copy")
        
        self.add_btn = QPushButton("Add Task")
        self.add_btn.clicked.connect(self.accept)
        
        # Layout organization
        h_layout_source = QHBoxLayout()
        h_layout_source.addWidget(self.source_line)
        h_layout_source.addWidget(self.source_btn)

        h_layout_dest = QHBoxLayout()
        h_layout_dest.addWidget(self.dest_line)
        h_layout_dest.addWidget(self.dest_btn)

        layout.addRow("Source Folder:", h_layout_source)
        layout.addRow("Destination Folder:", h_layout_dest)
        layout.addRow("Operation Mode:", self.mode_combo)
        layout.addRow(self.add_btn)

        self.task_data = None

    def _browse_folder(self, line_edit):
        """Opens a file dialog to select a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)

    def accept(self):
        """Collects data and closes the dialog."""
        source = self.source_line.text().strip()
        destination = self.dest_line.text().strip()
        mode_data = self.mode_combo.currentData()
        mode_text = self.mode_combo.currentText().split(' ')[0] # E.g., "Verify" or "Copy"

        if not source or not destination:
            QMessageBox.warning(self, "Input Error", "Both source and destination folders must be selected.")
            return

        self.task_data = {
            'source': source,
            'destination': destination,
            'mode': mode_data,
            'name': f"Op: {mode_text} | From: {os.path.basename(source)} | To: {os.path.basename(destination)}"
        }
        super().accept()

# =====================================================================
# Main Application Window
# =====================================================================

class FileCopierApp(QMainWindow):
    """Main application window for batch file operations."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Batch File Copier/Mover (MD5 Verified)")
        self.setGeometry(100, 100, 800, 600)

        # State and Data
        self.task_list = []
        self.worker_thread = None
        self.current_task_index = -1

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Initializes all UI components."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # 1. Task Management Section (Top)
        task_management_layout = QHBoxLayout()
        
        self.add_task_btn = QPushButton("➕ Add Task")
        self.add_task_btn.clicked.connect(self._add_task)
        
        self.remove_task_btn = QPushButton("➖ Remove Selected")
        self.remove_task_btn.clicked.connect(self._remove_task)
        
        self.start_btn = QPushButton("▶️ Start All Operations")
        self.start_btn.clicked.connect(self._start_operations)
        
        self.stop_btn = QPushButton("⏹️ Stop Operations")
        self.stop_btn.clicked.connect(self._stop_operations)
        self.stop_btn.setEnabled(False) # Disable initially
        
        task_management_layout.addWidget(self.add_task_btn)
        task_management_layout.addWidget(self.remove_task_btn)
        task_management_layout.addStretch()
        task_management_layout.addWidget(self.start_btn)
        task_management_layout.addWidget(self.stop_btn)

        main_layout.addLayout(task_management_layout)
        main_layout.addWidget(QLabel("Operation Queue:"))
        
        # 2. Task List Display
        self.task_list_widget = QListWidget()
        main_layout.addWidget(self.task_list_widget)

        # 3. Status and Progress Section (Bottom)
        main_layout.addWidget(QLabel("Current Task Status:"))
        
        # Current file being processed
        self.current_file_label = QLabel("File: N/A")
        self.current_file_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.current_file_label)
        
        # Detailed status (Copying, Verifying, Deleting)
        self.status_detail_label = QLabel("Status: Ready")
        main_layout.addWidget(self.status_detail_label)
        
        # Overall progress bar for the current task
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("Current Task: %p%")
        main_layout.addWidget(self.progress_bar)

    # --- Task Management Methods ---

    def _add_task(self):
        """Opens a dialog to create and add a new task to the list."""
        dialog = TaskSetupDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.task_data:
            # Add to internal list
            self.task_list.append(dialog.task_data)
            # Add to UI list widget
            self.task_list_widget.addItem(f"[{len(self.task_list)}] {dialog.task_data['name']}")
            
    def _remove_task(self):
        """Removes the selected task from the list."""
        selected_items = self.task_list_widget.selectedItems()
        if not selected_items:
            return

        # Get the index of the first selected item
        row = self.task_list_widget.row(selected_items[0])
        
        # Remove from internal data list
        if 0 <= row < len(self.task_list):
            del self.task_list[row]
        
        # Remove from UI list
        self.task_list_widget.takeItem(row)
        
        # Update the numbers in the remaining tasks (optional but good practice)
        self._update_task_list_ui()
        
    def _update_task_list_ui(self):
        """Refreshes the task numbering in the list widget."""
        self.task_list_widget.clear()
        for i, task in enumerate(self.task_list):
            self.task_list_widget.addItem(f"[{i+1}] {task['name']}")

    # --- Operation Control Methods ---

    def _start_operations(self):
        """Initiates the batch file operations."""
        if not self.task_list:
            QMessageBox.information(self, "No Tasks", "Please add at least one file operation task.")
            return

        if self.worker_thread is not None and self.worker_thread.isRunning():
            QMessageBox.information(self, "Running", "Operations are already in progress.")
            return

        # Reset UI
        self.current_task_index = -1
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.current_file_label.setText("File: Starting...")
        self.status_detail_label.setText("Status: Starting batch operation.")
        
        # Create and start the worker thread
        self.worker_thread = FileOperationWorker(self.task_list)
        
        # Connect signals
        self.worker_thread.overall_progress.connect(self._update_progress)
        self.worker_thread.operation_progress.connect(self._update_status)
        self.worker_thread.operation_finished.connect(self._handle_task_completion)
        self.worker_thread.finished.connect(self._thread_cleanup)
        
        self.worker_thread.start()
        
    def _stop_operations(self):
        """Stops the worker thread."""
        if self.worker_thread is not None and self.worker_thread.isRunning():
            reply = QMessageBox.question(self, 'Stop Confirmation',
                "Are you sure you want to stop the current batch operation?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.worker_thread.stop()
                self.status_detail_label.setText("Status: Stopping worker thread...")
                self.worker_thread.wait() # Wait for the thread to finish gracefully

    # --- Slot Methods for Thread Signals ---

    def _update_progress(self, percentage):
        """Updates the overall progress bar for the current task."""
        self.progress_bar.setValue(percentage)

    def _update_status(self, task_index, filename, message):
        """Updates detailed status labels."""
        self.current_task_index = task_index # Store the index of the task currently running
        task_name = self.task_list[task_index]['name']
        self.current_file_label.setText(f"Task [{task_index + 1}] - {task_name}: {filename}")
        self.status_detail_label.setText(f"Status: {message}")

    def _handle_task_completion(self, task_index, success, message):
        """Handles the completion of a single task."""
        if task_index < 0 or task_index >= len(self.task_list):
            return # Should not happen

        # Update the task list item in the UI to reflect completion/failure
        list_item = self.task_list_widget.item(task_index)
        
        if success:
            list_item.setText(list_item.text() + " **[DONE: Success]**")
            list_item.setForeground(Qt.GlobalColor.darkGreen)
        else:
            list_item.setText(list_item.text() + f" **[FAILED: {message}]**")
            list_item.setForeground(Qt.GlobalColor.red)
            # Stop the entire batch on failure (optional, but safer for secure moves)
            self._stop_operations() 

    def _thread_cleanup(self):
        """Final cleanup when the worker thread terminates."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.current_file_label.setText("File: N/A")
        
        if self.worker_thread.isRunning():
            self.status_detail_label.setText("Status: **Stopped by user.**")
        elif self.progress_bar.value() == 100:
             self.status_detail_label.setText("Status: **Batch Operation Complete!**")
        else:
             self.status_detail_label.setText("Status: **Batch Operation Finished (Errors or Stop)**")

        self.worker_thread = None

    def closeEvent(self, event):
        """Handles closing the main window, ensuring the thread is stopped."""
        if self.worker_thread is not None and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait() # Wait for the thread to stop
        event.accept()

# =====================================================================
# Application Entry Point
# =====================================================================

if __name__ == '__main__':
    # Add a simple check for the required modules
    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        print("PyQt5 is not installed. Please install it using: pip install PyQt5")
        sys.exit(1)
        
    app = QApplication(sys.argv)
    window = FileCopierApp()
    window.show()
    sys.exit(app.exec_())