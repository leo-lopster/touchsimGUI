from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog, QLabel, QMessageBox, QVBoxLayout
)

# ------------------------------------------------------------
# Image Viewer
# ------------------------------------------------------------

class ImageApp(QDialog):
    def __init__(self, directory):
        super().__init__()
        self.file_path = directory
        self.setWindowTitle("PyQt5 Image Viewer")
        self.setGeometry(100, 100, 350, 400)
        self.initUI()

    def initUI(self):
        # Label to display the image
        self.image_label = QLabel(self)
        # Center the image within the label's area
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setGeometry(10, 50, 400, 400)
        # Optional: Add a border to the label for visibility
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.open_image()

    def open_image(self):
        if self.file_path:
            # Create a QPixmap object from the selected file path
            print('>> Creating Pixmap')
            pixmap = QPixmap(self.file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "Image Not Found", "No image found on file path.")

            else:            
                # Scale the pixmap to fit the label while maintaining aspect ratio
                # Use scaledContents to automatically resize the pixmap to fit the label's size
                self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.image_label.setScaledContents(True) # Keep aspect ratio when resizing window
                
                layout = QVBoxLayout()
                layout.addWidget(self.image_label)
                self.setLayout(layout)
                self.exec()

        else:
            QMessageBox.warning(self, "No File Path", "No file path to image provided.")