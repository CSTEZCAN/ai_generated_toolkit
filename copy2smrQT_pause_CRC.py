#CAUTION! this code usually crashes over 100k files and CRC is pure cosmetics, do not copy, move and delete sensitive data. YOU HAVE BEEN WARNED!
import os
import time
import shutil
import sys
import zlib
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QMutex, QWaitCondition
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QProgressBar, QTextEdit, QLineEdit, QFileDialog
)

# --- CONFIGURATION DEFAULTS ---
SPEED_THRESHOLD_MB = 50.0  # Threshold in MB/s
CHUNK_SIZE = 1024 * 1024 * 4  # 4MB chunks for smooth writing
COOL_DOWN_STAGES = [10, 20, 30, 120] 


class CopyWorker(QThread):
    """Worker thread that processes the files without freezing the PyQt GUI."""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, float)  # percentage, current_speed
    file_changed_signal = pyqtSignal(str, str)  # filename, file_index_info
    finished_signal = pyqtSignal(str)

    def __init__(self, source_dir, dest_dir):
        super().__init__()
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.graceful_exit_requested = False
        self.bytes_copied = 0
        self.is_file_running = False
        
        # Thread synchronization for Pause/Resume feature
        self.is_paused = False
        self.mutex = QMutex()
        self.pause_condition = QWaitCondition()

    def pause(self):
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()

    def resume(self):
        self.mutex.lock()
        self.is_paused = False
        self.pause_condition.wakeAll()
        self.mutex.unlock()

    def check_paused_state(self):
        """Helper to pause execution mid-chunk if requested."""
        self.mutex.lock()
        while self.is_paused:
            self.pause_condition.wait(self.mutex)
        self.mutex.unlock()

    def fast_sampled_crc_check(self, src_path, dest_path):
        """
        Performs a rapid validation check across 100 sample intervals 
        up to a maximum chunk size of 1MB per sample block.
        """
        try:
            src_size = os.path.getsize(src_path)
            dest_size = os.path.getsize(dest_path)
            
            if src_size != dest_size:
                return False

            # If the file is incredibly small, just read and hash the whole thing
            if src_size <= 1024 * 64:  # Under 64KB
                with open(src_path, 'rb') as fs, open(dest_path, 'rb') as fd:
                    return zlib.crc32(fs.read()) == zlib.crc32(fd.read())

            # Determine dynamic sample dimensions
            num_samples = 100
            # Target 1/100th size chunk but cap it dynamically between 8KB and 1MB
            sample_chunk_size = max(8192, min(1024 * 1024, src_size // num_samples))
            
            # Create a uniform spacing step index
            if src_size > sample_chunk_size:
                step = (src_size - sample_chunk_size) // num_samples
            else:
                step = 0

            src_crc = 0
            dest_crc = 0

            with open(src_path, 'rb') as fsrc, open(dest_path, 'rb') as fdest:
                for i in range(num_samples):
                    self.check_paused_state()  # Ensure user can pause during long CRC queues
                    
                    offset = i * step
                    
                    # Read sample block from source file
                    fsrc.seek(offset)
                    src_chunk = fsrc.read(sample_chunk_size)
                    src_crc = zlib.crc32(src_chunk, src_crc)

                    # Read corresponding sample block from destination file
                    fdest.seek(offset)
                    dest_chunk = fdest.read(sample_chunk_size)
                    dest_crc = zlib.crc32(dest_chunk, dest_crc)
                    
                    if not src_chunk:
                        break

            return src_crc == dest_crc
        except Exception as e:
            self.log_signal.emit(f"  ⚠️ Error during CRC sampling calculation: {e}")
            return False

    def run(self):
        self.graceful_exit_requested = False
        
        if not os.path.exists(self.source_dir):
            self.log_signal.emit(f"❌ Source directory {self.source_dir} does not exist!")
            self.finished_signal.emit("Failed: Source missing")
            return

        self.log_signal.emit("Scanning source directory structure...")
        all_files = []
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                all_files.append(os.path.join(root, file))
                
        total_files = len(all_files)
        self.log_signal.emit(f"Found {total_files} total files across the tree structure.\n")
        
        slow_count_streak = 0
        
        for index, src_file in enumerate(all_files, start=1):
            self.check_paused_state()  # Guard check before starting a new file
            
            if self.graceful_exit_requested:
                self.log_signal.emit("🛑 Execution halted cleanly between files by user request.")
                break

            rel_path = os.path.relpath(src_file, self.source_dir)
            dest_file = os.path.join(self.dest_dir, rel_path)
            dest_folder = os.path.dirname(dest_file)
            
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
                
            file_name = os.path.basename(src_file)
            index_info = f"[{index}/{total_files}]"
            self.file_changed_signal.emit(file_name, index_info)
            self.log_signal.emit(f"{index_info} Tree: ...\\{rel_path}")
            
            # Pre-copy verification
            if os.path.exists(dest_file):
                src_size = os.path.getsize(src_file)
                dest_size = os.path.getsize(dest_file)
                
                if dest_size != src_size:
                    self.log_signal.emit(f"  ⚡ Size discrepancy detected (Dest: {dest_size}B vs Src: {src_size}B). Deleting file to restart transfer...")
                    try:
                        os.remove(dest_file)
                    except Exception as e:
                        self.log_signal.emit(f"  ❌ Error clearing broken file: {e}. Skipping for safety.")
                        self.log_signal.emit("-" * 50)
                        continue
                else:
                    # Run fast verification check if matching structural dimensions exist on target space
                    self.log_signal.emit("  🔍 Running Fast Sampled CRC Verification check...")
                    if self.fast_sampled_crc_check(src_file, dest_file):
                        self.log_signal.emit("Skipping (File already fully copied and verified).")
                        self.log_signal.emit("-" * 50)
                        continue
                    else:
                        self.log_signal.emit("  ❌ Fast CRC check failed! Destination file content mismatch. Re-copying file...")
                        try:
                            os.remove(dest_file)
                        except Exception as e:
                            self.log_signal.emit(f"  ❌ Error clearing corrupt file: {e}. Skipping.")
                            self.log_signal.emit("-" * 50)
                            continue
                
            try:
                # Perform the copy while monitoring speed
                was_slow = self.copy_and_monitor(src_file, dest_file)
                
                # Verify immediately after copying
                self.log_signal.emit("  🔍 Verifying newly copied file...")
                if self.fast_sampled_crc_check(src_file, dest_file):
                    self.log_signal.emit("  ✅ Verification successful.")
                else:
                    self.log_signal.emit("  ❌ Post-copy validation failed! Target write may be unstable.")

                if was_slow:
                    stage = min(slow_count_streak, len(COOL_DOWN_STAGES) - 1)
                    sleep_time = COOL_DOWN_STAGES[stage]
                    
                    self.log_signal.emit(f"💤 SMR drive cache saturated. Cool-down active: Waiting {sleep_time // 60} minute(s)...")
                    
                    cool_down_start = time.time()
                    while time.time() - cool_down_start < sleep_time:
                        self.check_paused_state()  # Guard check inside cool down
                        time.sleep(0.5)
                        if self.graceful_exit_requested:
                            break
                    
                    slow_count_streak += 1
                else:
                    if slow_count_streak > 0:
                        self.log_signal.emit("🚀 Speed stayed high! Resetting cool-down penalty tracker.")
                    slow_count_streak = 0
                    
            except Exception as e:
                self.log_signal.emit(f"❌ Error during copy: {e}")
                
            self.log_signal.emit("-" * 50)

        if self.graceful_exit_requested:
            self.finished_signal.emit("Stopped Safely")
        else:
            self.finished_signal.emit("Completed Successfully")

    def copy_and_monitor(self, src_path, dest_path):
        """Copies file data chunks and tracks metrics synchronously inside the thread."""
        total_bytes = os.path.getsize(src_path)
        self.bytes_copied = 0
        self.is_file_running = True
        triggered_slowdown = False
        
        self.log_signal.emit(f"Copying: {os.path.basename(src_path)} ({total_bytes / (1024**3):.2f} GB)")
        
        last_bytes = 0
        consecutive_slow_ticks = 0
        last_tick_time = time.time()

        with open(src_path, 'rb') as fsrc, open(dest_path, 'wb') as fdst:
            while self.is_file_running:
                self.check_paused_state()  # Guard check mid-file chunk copy
                
                buf = fsrc.read(CHUNK_SIZE)
                if not buf:
                    break
                fdst.write(buf)
                self.bytes_copied += len(buf)

                # Track metrics dynamically based on time steps
                now = time.time()
                if now - last_tick_time >= 1.0:
                    time_delta = now - last_tick_time
                    current_bytes = self.bytes_copied
                    bytes_delta = current_bytes - last_bytes
                    
                    speed_mb_s = (bytes_delta / (1024 * 1024)) / time_delta
                    percent = int((current_bytes / total_bytes) * 100) if total_bytes > 0 else 0
                    
                    self.progress_signal.emit(percent, speed_mb_s)
                    
                    # SMR Slowdown check
                    if speed_mb_s < SPEED_THRESHOLD_MB and 0 < current_bytes < total_bytes:
                        consecutive_slow_ticks += 1
                        if consecutive_slow_ticks >= 3 and not triggered_slowdown:
                            self.log_signal.emit(f"\n  ⚠️ Speed dropped to {speed_mb_s:.2f} MB/s (Below {SPEED_THRESHOLD_MB} MB/s threshold!)")
                            triggered_slowdown = True
                    else:
                        consecutive_slow_ticks = 0

                    last_bytes = current_bytes
                    last_tick_time = now

        shutil.copystat(src_path, dest_path)
        self.progress_signal.emit(100, 0.0) # Reset UI updates for this file
        return triggered_slowdown


class SmrBackupGUI(QMainWindow):
    """Main application Window for the PyQt5 GUI."""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None
        self.log_file_path = None
        
        # State tracking to compute speeds inline inside log writer
        self.current_file_start_time = None
        self.current_file_size_mb = 0.0

    def init_ui(self):
        self.setWindowTitle("SMR Safe Drive Cloner")
        self.resize(700, 550)

        # Central Widget layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Directory Inputs
        dir_layout = QVBoxLayout()
        
        # Source row
        src_row = QHBoxLayout()
        src_row.addWidget(QLabel("Source Directory: "))
        self.src_input = QLineEdit(SOURCE_DIR)
        src_row.addWidget(self.src_input)
        src_btn = QPushButton("Browse")
        src_btn.clicked.connect(lambda: self.browse_directory(self.src_input))
        src_row.addWidget(src_btn)
        dir_layout.addLayout(src_row)

        # Dest row
        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel("Destination Directory: "))
        self.dest_input = QLineEdit(DEST_DIR)
        dest_row.addWidget(self.dest_input)
        dest_btn = QPushButton("Browse")
        dest_btn.clicked.connect(lambda: self.browse_directory(self.dest_input))
        dest_row.addWidget(dest_btn)
        dir_layout.addLayout(dest_row)
        
        main_layout.addLayout(dir_layout)

        # Progress Indicators
        self.file_label = QLabel("Current File: None")
        main_layout.addWidget(self.file_label)

        progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_row.addWidget(self.progress_bar)
        
        self.speed_label = QLabel("Speed: 0.00 MB/s")
        self.speed_label.setFixedWidth(130)
        progress_row.addWidget(self.speed_label)
        main_layout.addLayout(progress_row)

        # Log Output Viewer
        main_layout.addWidget(QLabel("Process Logs:"))
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        main_layout.addWidget(self.log_viewer)

        # Operational Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Transfer")
        self.start_btn.clicked.connect(self.start_transfer)
        btn_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        btn_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("Stop Transfer")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_transfer)
        btn_layout.addWidget(self.stop_btn)

        main_layout.addLayout(btn_layout)

    def browse_directory(self, line_edit_widget):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            line_edit_widget.setText(os.path.normpath(directory))

    def start_transfer(self):
        src = self.src_input.text().strip()
        dest = self.dest_input.text().strip()

        if not src or not dest:
            self.log_viewer.append("❌ Source or Destination paths cannot be empty!")
            return

        # Prepare log directory setup
        if not os.path.exists(dest):
            try:
                os.makedirs(dest)
            except Exception as e:
                self.log_viewer.append(f"❌ Failed to create Destination: {e}")
                return
        
        self.log_file_path = os.path.join(dest, "copy_log.txt")

        # UI State updates
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText("Pause")
        self.stop_btn.setEnabled(True)
        self.src_input.setEnabled(False)
        self.dest_input.setEnabled(False)
        self.log_viewer.clear()

        # State resets
        self.current_file_start_time = None
        self.current_file_size_mb = 0.0

        # Thread Init
        self.worker = CopyWorker(src, dest)
        self.worker.log_signal.connect(self.handle_log)
        self.worker.progress_signal.connect(self.handle_progress)
        self.worker.file_changed_signal.connect(self.handle_file_change)
        self.worker.finished_signal.connect(self.handle_finished)
        self.worker.start()

    def toggle_pause(self):
        if self.worker and self.worker.isRunning():
            if not self.worker.is_paused:
                self.worker.pause()
                self.pause_btn.setText("Resume")
                self.log_viewer.append("\n⏸️ Transfer paused by user.")
            else:
                self.worker.resume()
                self.pause_btn.setText("Pause")
                self.log_viewer.append("\n▶️ Transfer resumed.")

    def stop_transfer(self):
        if self.worker and self.worker.isRunning():
            self.log_viewer.append("\n⚠️ Stop requested! Safely writing out the current file...")
            self.stop_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.worker.stop()

    def handle_log(self, text):
        self.log_viewer.append(text)
        
        # Save to disk log file simultaneously
        if self.log_file_path:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            clean_msg = text.replace("📊 ", "").replace("⚠️ ", "").replace("💤 ", "").replace("🚀 ", "").replace("🔍 ", "").replace("✅ ", "")
            
            # Catch initialization of a new file copy to capture size & start time
            if "Copying:" in clean_msg:
                self.current_file_start_time = time.time()
                try:
                    size_part = clean_msg.split("(")[-1].replace(")", "").strip()
                    val, unit = size_part.split()
                    val = float(val)
                    if "GB" in unit:
                        val *= 1024
                    elif "KB" in unit:
                        val /= 1024
                    elif "Bytes" in unit:
                        val /= (1024 * 1024)
                    self.current_file_size_mb = val
                except Exception:
                    self.current_file_size_mb = 0.0

            if clean_msg.strip():
                try:
                    # Insert Calculated overall speed log right before writing the closing divider
                    if "--------------------------------------------------" in clean_msg and self.current_file_start_time:
                        duration = time.time() - self.current_file_start_time
                        if self.current_file_size_mb > 0 and duration > 0:
                            calc_speed = self.current_file_size_mb / duration
                            speed_log = f"[{timestamp}] Average Transfer Speed: {calc_speed:.2f} MB/s (Completed in {int(duration)}s)\n"
                            with open(self.log_file_path, "a", encoding="utf-8") as f:
                                f.write(speed_log)
                        self.current_file_start_time = None # Reset
                    
                    with open(self.log_file_path, "a", encoding="utf-8") as f:
                        f.write(f"[{timestamp}] {clean_msg}\n")
                except Exception:
                    pass

    def handle_progress(self, percent, speed):
        self.progress_bar.setValue(percent)
        self.speed_label.setText(f"Speed: {speed:.2f} MB/s")

    def handle_file_change(self, file_name, file_index_info):
        self.file_label.setText(f"Current File {file_index_info}: {file_name}")

    def handle_finished(self, status_msg):
        self.log_viewer.append(f"\n🏁 Status: {status_msg}")
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("Pause")
        self.stop_btn.setEnabled(False)
        self.src_input.setEnabled(True)
        self.dest_input.setEnabled(True)
        self.progress_bar.setValue(0)
        self.speed_label.setText("Speed: 0.00 MB/s")
        self.file_label.setText("Current File: None")


if __name__ == "__main__":
    SOURCE_DIR = globals().get('SOURCE_DIR', r"J:\BEE_2")
    DEST_DIR = globals().get('DEST_DIR', r"F:\BEE_2")

    app = QApplication(sys.argv)
    window = SmrBackupGUI()
    window.show()
    sys.exit(app.exec_())
