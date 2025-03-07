import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                           QRadioButton, QButtonGroup, QProgressBar, 
                           QMessageBox, QFrame, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from invoiceApp import InvoiceApp
from logger import Logger


class WorkerThread(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, invoice_app, mode, file):
        super().__init__()
        self.invoice_app = invoice_app
        self.mode = mode
        self.file = file
        
    def run(self):
        result = self.invoice_app.run()
        self.finished.emit(result)


class ModernInvoiceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = Logger.get_logger(__name__)
        self.invoice_app = None
        self.selected_file = ""
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Green Invoice Automation')
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QGroupBox {
                border: 2px solid #dcdde1;
                border-radius: 8px;
                margin-top: 1em;
                padding: 20px;
                background-color: white;
            }
            QGroupBox::title {
                color: #2f3640;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #00a8ff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                min-width: 120px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0097e6;
            }
            QPushButton:pressed {
                background-color: #00a8ff;
            }
            QRadioButton {
                spacing: 12px;
                color: #2f3640;
                padding: 8px;
                font-size: 13px;
                margin: 4px 0;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QProgressBar {
                border: 2px solid #dcdde1;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #00a8ff;
            }
            QLabel {
                color: #2f3640;
                font-size: 13px;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(25)  # Increased spacing between major sections
        main_layout.setContentsMargins(30, 30, 30, 30)  # Increased margins
        
        # File Selection Group
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout()
        file_layout.setContentsMargins(15, 15, 15, 15)  # Added internal padding
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #7f8fa6; padding: 0 10px;")
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(120)  # Fixed width for consistency
        
        file_layout.addWidget(self.file_label, stretch=1)
        file_layout.addWidget(browse_btn)
        file_group.setLayout(file_layout)
        
        # Mode Selection Group
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QVBoxLayout()
        mode_layout.setContentsMargins(15, 15, 15, 15)  # Added internal padding
        mode_layout.setSpacing(12)  # Increased spacing between radio buttons
        
        self.mode_group = QButtonGroup()
        modes = [
            ('Check Client', 'checkClient'),
            ('Preview Invoice', 'preview'),
            ('Generate Invoice', 'generate')
        ]
        for i, (display_text, mode_value) in enumerate(modes):
            radio = QRadioButton(display_text)
            radio.setProperty('mode_value', mode_value)  # Store actual mode value
            if i == 0:
                radio.setChecked(True)
            self.mode_group.addButton(radio)
            mode_layout.addWidget(radio)
        
        # Add stretch to center radio buttons vertically
        mode_layout.addStretch(1)
        mode_group.setLayout(mode_layout)
        
        # Progress Section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(15, 15, 15, 15)  # Added internal padding
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.hide()
        
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        
        # Action Button
        self.run_button = QPushButton("Run")
        self.run_button.setFixedHeight(45)  # Increased height
        self.run_button.setFixedWidth(200)  # Set fixed width
        
        # Center the run button
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.run_button)
        button_layout.addStretch(1)
        
        # Add all components to main layout
        main_layout.addWidget(file_group)
        main_layout.addWidget(mode_group)
        main_layout.addWidget(progress_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)  # Add stretch at the bottom
        
        # Set window size and position
        self.setFixedSize(600, 600)  # Increased window size
        self.center_window()
        
        # Connect signals
        browse_btn.clicked.connect(self.browse_file)
        self.run_button.clicked.connect(self.run_mode)
        
        self.logger.debug("ModernInvoiceApp UI initialized")
        
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        
    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",  # More descriptive title
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file:
            self.selected_file = file
            self.file_label.setText(file.split('/')[-1])
            self.logger.debug(f"Selected file: {file}")
            
    def run_mode(self):
        if not self.selected_file:
            QMessageBox.warning(
                self,
                "No File Selected",
                "Please select an Excel file before proceeding."
            )
            return
            
        selected_radio = self.mode_group.checkedButton()
        mode = selected_radio.property('mode_value')  # Get the actual mode value
        self.logger.debug(f"Running mode: {mode} with file: {self.selected_file}")
        
        self.progress_bar.show()
        self.run_button.setEnabled(False)
        
        self.invoice_app = InvoiceApp(mode, self.selected_file)
        self.worker = WorkerThread(self.invoice_app, mode, self.selected_file)
        self.worker.finished.connect(self.handle_result)
        self.worker.start()
        
    def handle_result(self, result):
        self.progress_bar.hide()
        self.run_button.setEnabled(True)
        
        selected_radio = self.mode_group.checkedButton()
        mode = selected_radio.property('mode_value')
        self.logger.debug(f"Handling result for mode: {mode}")
        
        if mode == 'checkClient':
            if result:
                missing_clients_str = "\n".join(result)
                reply = QMessageBox.question(
                    self,
                    "Missing Clients Found",
                    f"The following clients are missing:\n\n{missing_clients_str}\n\nWould you like to add them?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    for missing_client in result:
                        self.invoice_app.handle_missing_clients(missing_client)
                    QMessageBox.information(self, "Success", "Clients have been added successfully.")
        else:
            QMessageBox.information(
                self,
                "Operation Complete",
                str(result)
            )


def main():
    app = QApplication(sys.argv)
    ex = ModernInvoiceApp()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
