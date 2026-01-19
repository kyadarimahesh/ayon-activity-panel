"""Library utilities for Activity Panel."""

from contextlib import contextmanager


@contextmanager
def qt_app_context():
    """Qt application context manager.
    
    Ensures Qt application exists before showing windows.
    """
    try:
        from qtpy.QtWidgets import QApplication
    except ImportError:
        from PySide2.QtWidgets import QApplication

    try:
        from ayon_core.style import load_stylesheet
    except ImportError:
        load_stylesheet = None

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        # Apply AYON stylesheet to application
        if load_stylesheet:
            app.setStyleSheet(load_stylesheet())

    yield app
