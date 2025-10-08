import sys
import fitz  # PyMuPDF
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QFileDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import Qt, QPoint


class PDFReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Reader")
        self.setGeometry(100, 100, 800, 600)

        self.pdf_document = None
        self.current_page = 0
        self.zoom_factor = 1.0  # Zoom level (initially 1x)
        self.dragging = False
        self.drag_start = QPoint()

        # Setup the UI
        self.init_ui()

    def init_ui(self):
        # Create a QWidget to hold everything
        widget = QWidget(self)
        self.setCentralWidget(widget)

        # Layouts
        layout = QVBoxLayout()
        nav_layout = QHBoxLayout()

        # Navigation buttons
        self.prev_btn = QPushButton('Previous', self)
        self.prev_btn.clicked.connect(self.go_previous)

        self.next_btn = QPushButton('Next', self)
        self.next_btn.clicked.connect(self.go_next)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)

        # Graphics View for PDF rendering
        self.view = QGraphicsView(self)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        # Graphics Scene for displaying the PDF
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)

        layout.addWidget(self.view)
        layout.addLayout(nav_layout)

        widget.setLayout(layout)

        # Open PDF Button
        open_pdf_btn = QPushButton("Open PDF", self)
        open_pdf_btn.clicked.connect(self.open_pdf)
        layout.addWidget(open_pdf_btn)

    def open_pdf(self):
        # Open file dialog to select a PDF
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("PDF Files (*.pdf)")  # Use setNameFilter() instead
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        # Load the PDF document
        self.pdf_document = fitz.open(file_path)
        self.current_page = 0
        self.zoom_factor = 1.0  # Reset zoom when a new document is loaded
        self.show_page(self.current_page)

    def show_page(self, page_number):
        if self.pdf_document:
            page = self.pdf_document.load_page(page_number)
            pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_factor, self.zoom_factor))  # Apply zoom factor
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            # Create a pixmap item to add to the scene
            self.scene.clear()  # Clear previous page
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.pixmap_item)
            self.view.setScene(self.scene)

    def go_previous(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def go_next(self):
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def wheelEvent(self, event):
        # Scroll up/down (next/previous page) with Mouse Wheel
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:  # Scroll up (Zoom In)
                self.zoom_in()
            elif event.angleDelta().y() < 0:  # Scroll down (Zoom Out)
                self.zoom_out()
        else:
            if event.angleDelta().y() > 0:  # Scroll up (Next page)
                self.go_next()
            elif event.angleDelta().y() < 0:  # Scroll down (Previous page)
                self.go_previous()

    def keyPressEvent(self, event):
        # Handle Up/Down Arrow or Page Up/Page Down keys
        if event.key() == Qt.Key_Up:  # Arrow Up (Previous page)
            self.go_previous()
        elif event.key() == Qt.Key_Down:  # Arrow Down (Next page)
            self.go_next()
        elif event.key() == Qt.Key_PageUp:  # Page Up (Previous page)
            self.go_previous()
        elif event.key() == Qt.Key_PageDown:  # Page Down (Next page)
            self.go_next()

    def zoom_in(self):
        self.zoom_factor *= 1.2  # Increase zoom level by 20%
        self.show_page(self.current_page)

    def zoom_out(self):
        self.zoom_factor /= 1.2  # Decrease zoom level by 20%
        self.show_page(self.current_page)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.pos() - self.drag_start
            self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().value() - delta.x())
            self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().value() - delta.y())
            self.drag_start = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PDFReader()
    window.show()
    sys.exit(app.exec_())
