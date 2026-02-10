"""Pure Python UI for Activity Panel - No .ui files needed."""
from __future__ import annotations

from qtpy import QtCore, QtWidgets
from ayon_core.style import load_stylesheet


class ActivityPanelUI:
    """UI builder for Activity Panel."""

    def __init__(self) -> None:
        """Initialize UI builder."""
        # Widgets that need to be accessed
        self.mainSplitter = None
        self.versionDetailsLayout = None
        self.versionGridLayout = None
        self.pathLabel_value = None
        self.versionLabel = None
        self.versionComboBox = None
        self.statusLabel = None
        self.statusComboBox = None
        self.authorLabel = None
        self.authorLineEdit = None
        self.contentTabWidget = None
        self.allActivityButton = None
        self.commentsButton = None
        self.publishedVersionsButton = None
        self.checklistsButton = None
        self.refreshButton = None
        self.textBrowser_activity_panel = None
        self.textEdit_comment = None
        self.pushButton_comment = None
        self.buttonLayout = None
        self.representationsTabLayout = None

    def setupUi(self, parent_widget: QtWidgets.QWidget) -> None:
        """Build UI programmatically.
        
        Args:
            parent_widget: Parent widget to setup UI in.
        """
        parent_widget.setStyleSheet(load_stylesheet())

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(parent_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Main splitter (vertical)
        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        # Add sections
        self.mainSplitter.addWidget(self._create_version_details())
        self.mainSplitter.addWidget(self._create_content_tabs())
        self.mainSplitter.addWidget(self._create_comment_section())

        main_layout.addWidget(self.mainSplitter)

    def _create_version_details(self) -> QtWidgets.QWidget:
        """Create version details section.
        
        Returns:
            Widget containing version details UI.
        """
        widget = QtWidgets.QWidget()
        self.versionDetailsLayout = QtWidgets.QVBoxLayout(widget)
        self.versionDetailsLayout.setContentsMargins(0, 0, 0, 0)

        self.versionGridLayout = QtWidgets.QGridLayout()

        # Path
        self.versionGridLayout.addWidget(QtWidgets.QLabel("Path:"), 0, 0)
        self.pathLabel_value = QtWidgets.QLabel()
        self.pathLabel_value.setWordWrap(True)
        self.pathLabel_value.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.versionGridLayout.addWidget(self.pathLabel_value, 0, 1)

        # Version
        self.versionLabel = QtWidgets.QLabel("Version:")
        self.versionGridLayout.addWidget(self.versionLabel, 1, 0)
        self.versionComboBox = QtWidgets.QComboBox()
        self.versionGridLayout.addWidget(self.versionComboBox, 1, 1)

        # Status
        self.statusLabel = QtWidgets.QLabel("Status:")
        self.versionGridLayout.addWidget(self.statusLabel, 2, 0)
        self.statusComboBox = QtWidgets.QComboBox()
        self.versionGridLayout.addWidget(self.statusComboBox, 2, 1)

        # Author
        self.authorLabel = QtWidgets.QLabel("Author:")
        self.versionGridLayout.addWidget(self.authorLabel, 3, 0)
        self.authorLineEdit = QtWidgets.QLineEdit()
        self.authorLineEdit.setReadOnly(True)
        self.versionGridLayout.addWidget(self.authorLineEdit, 3, 1)

        self.versionDetailsLayout.addLayout(self.versionGridLayout)
        return widget

    def _create_content_tabs(self) -> QtWidgets.QTabWidget:
        """Create tabbed content.
        
        Returns:
            Tab widget with activity and representations tabs.
        """
        self.contentTabWidget = QtWidgets.QTabWidget()

        # Activity Tab
        activity_tab = QtWidgets.QWidget()
        activity_layout = QtWidgets.QVBoxLayout(activity_tab)

        # Filter buttons
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.setSpacing(2)

        self.allActivityButton = QtWidgets.QPushButton()
        self.allActivityButton.setCheckable(True)
        self.allActivityButton.setChecked(True)
        self.allActivityButton.setToolTip("All activity")

        self.commentsButton = QtWidgets.QPushButton()
        self.commentsButton.setCheckable(True)
        self.commentsButton.setToolTip("Comments")

        self.publishedVersionsButton = QtWidgets.QPushButton()
        self.publishedVersionsButton.setCheckable(True)
        self.publishedVersionsButton.setToolTip("Published versions")

        self.checklistsButton = QtWidgets.QPushButton()
        self.checklistsButton.setCheckable(True)
        self.checklistsButton.setToolTip("Checklists")

        self.refreshButton = QtWidgets.QPushButton()
        self.refreshButton.setCheckable(True)
        self.refreshButton.setToolTip("Refresh activities (Auto-refresh every 5 mins)")

        filter_layout.addWidget(self.allActivityButton)
        filter_layout.addWidget(self.commentsButton)
        filter_layout.addWidget(self.publishedVersionsButton)
        filter_layout.addWidget(self.checklistsButton)
        filter_layout.addWidget(self.refreshButton)
        filter_layout.addItem(
            QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        # Activity browser
        self.textBrowser_activity_panel = QtWidgets.QTextBrowser()

        activity_layout.addLayout(filter_layout)
        activity_layout.addWidget(self.textBrowser_activity_panel)

        # Representations Tab
        repre_tab = QtWidgets.QWidget()
        self.representationsTabLayout = QtWidgets.QVBoxLayout(repre_tab)
        self.representationsTabLayout.addItem(
            QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        self.contentTabWidget.addTab(activity_tab, "Activity")
        self.contentTabWidget.addTab(repre_tab, "Representations")

        return self.contentTabWidget

    def _create_comment_section(self) -> QtWidgets.QWidget:
        """Create comment input section.
        
        Returns:
            Widget containing comment input UI.
        """
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Comment input
        self.textEdit_comment = QtWidgets.QTextEdit()
        self.textEdit_comment.setPlaceholderText("Comment or mention with @user, @@version, @@@task...")

        # Button layout
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.addItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        self.pushButton_comment = QtWidgets.QPushButton("Comment")
        self.buttonLayout.addWidget(self.pushButton_comment)

        layout.addWidget(self.textEdit_comment)
        layout.addLayout(self.buttonLayout)

        return widget
