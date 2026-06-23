import sys
import os
import ftplib
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QListWidget, QAbstractItemView,
                             QGridLayout, QHBoxLayout, QVBoxLayout, QMessageBox, QInputDialog, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal

# Worker Thread for handling uploads cleanly without freezing the GUI
class FTPUploadWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, ftp, filenames):
        super().__init__()
        self.ftp = ftp
        self.filenames = filenames

    def run(self):
        try:
            for filename in self.filenames:
                file_size = os.path.getsize(filename)
                bytes_uploaded = 0

                # Callback function to track bytes sent
                def callback(chunk):
                    nonlocal bytes_uploaded
                    bytes_uploaded += len(chunk)
                    if file_size > 0:
                        percent = int((bytes_uploaded / file_size) * 100)
                        self.progress_signal.emit(percent)

                with open(filename, 'rb') as f:
                    self.ftp.storbinary(f'STOR {os.path.basename(filename)}', f, callback=callback)
            
            self.finished_signal.emit(True, "All files uploaded successfully!")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class FTPClientApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ftp = None
        self.upload_worker = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Advanced PyQt5 FTP/FTPS Client')
        self.resize(800, 550)
        
        # --- Connection Layout ---
        grid = QGridLayout()

        grid.addWidget(QLabel('IP / Host:'), 0, 0)
        self.ip_input = QLineEdit('192.168.1.1') 
        grid.addWidget(self.ip_input, 0, 1)
        
        grid.addWidget(QLabel('Port:'), 0, 2)
        self.port_input = QLineEdit('12345')
        grid.addWidget(self.port_input, 0, 3)
        
        grid.addWidget(QLabel('Username:'), 1, 0)
        self.user_input = QLineEdit('pc')
        grid.addWidget(self.user_input, 1, 1)
        
        grid.addWidget(QLabel('Password:'), 1, 2)
        self.pass_input = QLineEdit('000000')
        self.pass_input.setEchoMode(QLineEdit.Password)
        grid.addWidget(self.pass_input, 1, 3)
        
        self.ftps_checkbox = QCheckBox('Use FTPS (Explicit TLS)')
        grid.addWidget(self.ftps_checkbox, 2, 1)
        
        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.toggle_connection)
        grid.addWidget(self.connect_btn, 2, 3)
        
        # --- File Lists Layout ---
        lists_layout = QHBoxLayout()
        
        # Local Files
        local_vbox = QVBoxLayout()
        local_vbox.addWidget(QLabel('Local Directory Files (Ctrl/Shift to multi-select):'))
        self.local_list = QListWidget()
        # Enable Multi-Selection (Ctrl and Shift selection)
        self.local_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        local_vbox.addWidget(self.local_list)
        lists_layout.addLayout(local_vbox)
        
        # Remote Files
        remote_vbox = QVBoxLayout()
        remote_vbox.addWidget(QLabel('Remote FTP Files (Double-click folder to open):'))
        self.remote_list = QListWidget()
        self.remote_list.itemDoubleClicked.connect(self.on_remote_double_click)
        remote_vbox.addWidget(self.remote_list)
        lists_layout.addLayout(remote_vbox)
        
        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        # --- Action Buttons Layout ---
        actions_layout = QHBoxLayout()
        self.upload_btn = QPushButton('Upload Selected')
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self.start_upload)
        
        self.mkdir_btn = QPushButton('Create Folder')
        self.mkdir_btn.setEnabled(False)
        self.mkdir_btn.clicked.connect(self.create_remote_folder)
        
        exit_btn = QPushButton('Exit')
        exit_btn.clicked.connect(self.close)
        
        actions_layout.addWidget(self.upload_btn)
        actions_layout.addWidget(self.mkdir_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(exit_btn)
        
        # --- Main Layout Assembly ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addLayout(lists_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(actions_layout)
        
        self.setLayout(main_layout)
        self.update_local_list()

    def update_local_list(self):
        self.local_list.clear()
        try:
            files = [f for f in os.listdir('.') if os.path.isfile(f)]
            self.local_list.addItems(files)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Could not load local files: {e}")

    def toggle_connection(self):
        if self.ftp is None:
            self.connect_ftp()
        else:
            self.disconnect_ftp()

    def connect_ftp(self):
        host = self.ip_input.text()
        port = int(self.port_input.text())
        user = self.user_input.text()
        passwd = self.pass_input.text()
        
        try:
            if self.ftps_checkbox.isChecked():
                self.ftp = ftplib.FTP_TLS()
                self.ftp.connect(host, port)
                self.ftp.login(user, passwd)
                self.ftp.prot_p() 
            else:
                self.ftp = ftplib.FTP()
                self.ftp.connect(host, port)
                self.ftp.login(user, passwd)
                
            self.connect_btn.setText('Disconnect')
            self.upload_btn.setEnabled(True)
            self.mkdir_btn.setEnabled(True)
            self.update_remote_list()
            QMessageBox.information(self, 'Success', 'Connected successfully!')
            
        except Exception as e:
            QMessageBox.critical(self, 'Connection Error', str(e))
            self.ftp = None

    def disconnect_ftp(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                pass
            self.ftp = None
        self.connect_btn.setText('Connect')
        self.upload_btn.setEnabled(False)
        self.mkdir_btn.setEnabled(False)
        self.remote_list.clear()
        self.progress_bar.setValue(0)
        QMessageBox.information(self, 'Disconnected', 'Disconnected from server.')

    def update_remote_list(self):
        self.remote_list.clear()
        if not self.ftp:
            return
        try:
            self.remote_list.addItem("[ .. ]")
            files = self.ftp.nlst()
            for item in files:
                if item not in ['.', '..']:
                    self.remote_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch remote list: {e}")

    def on_remote_double_click(self, item):
        if not self.ftp:
            return
        target = item.text()
        if target == "[ .. ]":
            try:
                self.ftp.cwd("..")
                self.update_remote_list()
            except Exception as e:
                QMessageBox.warning(self, 'Navigation Error', f"Cannot move up: {e}")
            return

        try:
            self.ftp.cwd(target)
            self.update_remote_list()
        except ftplib.error_perm:
            pass  # It's a file, do nothing
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Error opening path: {e}")

    def create_remote_folder(self):
        if not self.ftp:
            return
        folder_name, ok = QInputDialog.getText(self, 'Create New Folder', 'Enter folder name:')
        if ok and folder_name:
            try:
                self.ftp.mkd(folder_name)
                QMessageBox.information(self, 'Success', f"Folder '{folder_name}' created successfully!")
                self.update_remote_list()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f"Could not create folder: {e}")

    def start_upload(self):
        selected_items = self.local_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Warning', 'Please select at least one local file to upload.')
            return
            
        filenames = [item.text() for item in selected_items]
        
        # Disable interface buttons to prevent conflicts during upload
        self.upload_btn.setEnabled(False)
        self.connect_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start background worker thread
        self.upload_worker = FTPUploadWorker(self.ftp, filenames)
        self.upload_worker.progress_signal.connect(self.progress_bar.setValue)
        self.upload_worker.finished_signal.connect(self.on_upload_finished)
        self.upload_worker.start()

    def on_upload_finished(self, success, message):
        self.upload_btn.setEnabled(True)
        self.connect_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, 'Success', message)
            self.progress_bar.setValue(100)
            self.update_remote_list()
        else:
            QMessageBox.critical(self, 'Upload Error', message)
            self.progress_bar.setValue(0)

    def closeEvent(self, event):
        self.disconnect_ftp()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FTPClientApp()
    ex.show()
    sys.exit(app.exec_())