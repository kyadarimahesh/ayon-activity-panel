"""Snipping widget for screen capture."""
from qtpy import QtWidgets, QtCore, QtGui

from ayon_core.lib import Logger

log = Logger.get_logger(__name__)


class SnippingWidget(QtWidgets.QWidget):
    """Widget for capturing a selected area of the screen."""

    closed = QtCore.Signal()

    def __init__(self, parent=None):
        super(SnippingWidget, self).__init__(parent)

        self.screen = QtWidgets.QApplication.primaryScreen()
        self.screenshot = self.screen.grabWindow(0)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.is_selecting = False
        self.captured_pixmap = None

        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Tool
        )
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setFocus()
        self.grabKeyboard()
        self.show()

    def paintEvent(self, event):
        """Paint the screen capture and selection rectangle."""
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.screenshot)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 100))

        if self.is_selecting and not self.begin.isNull() and not self.end.isNull():
            rect = QtCore.QRect(self.begin, self.end).normalized()
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            painter.fillRect(rect, QtCore.Qt.transparent)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            painter.drawPixmap(rect, self.screenshot, rect)

            pen = QtGui.QPen(QtGui.QColor(92, 173, 214), 2, QtCore.Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

            label_text = "{} x {}".format(rect.width(), rect.height())
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            label_rect = painter.fontMetrics().boundingRect(label_text)
            label_rect.adjust(-5, -5, 5, 5)
            label_pos = QtCore.QPoint(
                rect.left(), rect.top() - label_rect.height() - 5
            )
            if label_pos.y() < 0:
                label_pos.setY(rect.top() + 5)
            label_rect.moveTopLeft(label_pos)
            painter.fillRect(label_rect, QtGui.QColor(0, 0, 0, 180))
            painter.setPen(QtCore.Qt.white)
            painter.drawText(label_rect, QtCore.Qt.AlignCenter, label_text)

    def mousePressEvent(self, event):
        """Handle mouse press to start selection."""
        if event.button() == QtCore.Qt.RightButton:
            # Right-click to cancel
            self.captured_pixmap = None
            self.close()
            self.closed.emit()
        elif event.button() == QtCore.Qt.LeftButton:
            self.begin = event.pos()
            self.end = event.pos()
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move to update selection."""
        if self.is_selecting:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to complete selection."""
        if event.button() == QtCore.Qt.LeftButton and self.is_selecting:
            self.end = event.pos()
            self.is_selecting = False
            rect = QtCore.QRect(self.begin, self.end).normalized()
            if rect.width() > 0 and rect.height() > 0:
                self.captured_pixmap = self.screenshot.copy(rect)
                self.close()
                self.closed.emit()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == QtCore.Qt.Key_Escape:
            self.captured_pixmap = None
            self.releaseKeyboard()
            self.close()
            self.closed.emit()
        else:
            super(SnippingWidget, self).keyPressEvent(event)

    def closeEvent(self, event):
        """Handle widget close."""
        self.releaseKeyboard()
        super(SnippingWidget, self).closeEvent(event)

    def get_captured_image(self):
        """Return the captured pixmap."""
        return self.captured_pixmap
