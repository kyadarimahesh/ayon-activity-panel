"""Native Qt widget-based activity renderer matching AYON Web UI."""

from qtpy.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QGridLayout, QCheckBox
)
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QPixmap, QCursor

# Visual tokens matching AYON Web UI
COLORS = {
    'bg': '#1b232b',
    'card': '#202a33',
    'border': '#2d3842',
    'text': '#e0e6eb',
    'text_secondary': '#9aa4ad',
}


class ClickableLabel(QLabel):
    """Label that emits click signal with file_id and activity_index."""
    clicked = Signal(str, int)  # file_id, activity_index

    def __init__(self, file_id=None, activity_index=None, parent=None):
        super().__init__(parent)
        self._file_id = file_id
        self._activity_index = activity_index
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._file_id is not None:
            self.clicked.emit(self._file_id, self._activity_index)


class CommentCard(QFrame):
    """Comment card - contains message with inline styled tags and thumbnails."""

    def __init__(self, message, activity_index=None, parent=None):
        super().__init__(parent)
        self.activity_index = activity_index
        self.setObjectName("CommentCard")
        self.setStyleSheet(f"""
            #CommentCard {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setMinimumWidth(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 9, 9, 9)
        layout.setSpacing(7)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        msg_label.setOpenExternalLinks(True)
        msg_label.setTextFormat(Qt.RichText)
        msg_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 9pt;")
        msg_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(msg_label)

        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QGridLayout(self.thumbnail_widget)
        self.thumbnail_layout.setContentsMargins(0, 3, 0, 0)
        self.thumbnail_layout.setSpacing(0)
        self.thumbnail_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.thumbnail_count = 0
        layout.addWidget(self.thumbnail_widget)

    def add_thumbnail(self, pixmap, tooltip="", file_id="", filename=""):
        """Add thumbnail with filename to card in grid layout (max 3 per row)."""
        thumb_container = QWidget()
        thumb_container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setSpacing(2)

        thumb_label = ClickableLabel(file_id, self.activity_index)
        thumb_label.setPixmap(pixmap.scaled(94, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        thumb_label.setStyleSheet(f"""
            border: 1px solid {COLORS['border']};
            background-color: {COLORS['bg']};
            padding: 2px;
        """)
        thumb_label.setFixedSize(97, 63)
        if tooltip:
            thumb_label.setToolTip(tooltip)
        thumb_layout.addWidget(thumb_label)

        if filename:
            name_label = QLabel(filename)
            name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 7pt;")
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setWordWrap(False)
            name_label.setFixedWidth(97)
            thumb_layout.addWidget(name_label)

        row = self.thumbnail_count // 3
        col = self.thumbnail_count % 3
        self.thumbnail_layout.addWidget(thumb_container, row, col)
        self.thumbnail_count += 1

        return thumb_label


class WebLikeActivityRenderer(QScrollArea):
    """Native Qt activity renderer matching AYON Web UI."""

    thumbnail_clicked = Signal(str, int)
    checkbox_changed = Signal(str, str, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['bg']};
                border: none;
            }}
            QScrollBar:vertical {{
                width: 10px;
                background: {COLORS['bg']};
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        self.setMinimumWidth(150)

        self.container = QWidget()
        self.container.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.setWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(7, 7, 7, 7)
        self.main_layout.setSpacing(3)

        self._comment_cards = {}

    def clear(self):
        """Clear all activities."""
        while self.main_layout.count() > 0:
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._comment_cards.clear()

    def add_task_status_change(self, author, task_name, old_status, new_status,
                               timestamp, old_color=None, new_color=None):
        """Add task status change row."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        label = QLabel()
        old_status_html = f'<span style="color: {old_color};">{old_status}</span>' if old_color else old_status
        new_status_html = f'<span style="color: {new_color};">{new_status}</span>' if new_color else new_status

        text = (f'<span style="color: {COLORS["text"]};">{author}</span> '
                f'<span style="color: {COLORS["text_secondary"]};">{task_name} • </span>'
                f'{old_status_html} → {new_status_html}')

        label.setText(text)
        label.setStyleSheet(f"background-color: transparent; font-size: 8pt;")
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        layout.addWidget(label, 1)

        time_label = QLabel(f' • {timestamp}')
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        time_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        layout.addWidget(time_label, 0)

        container = QWidget()
        container.setLayout(layout)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        container.setMaximumHeight(20)
        self.main_layout.addWidget(container)

    def add_status_change(self, author, product, version, old_status, new_status,
                          timestamp, old_color=None, new_color=None):
        """Add status change row."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        label = QLabel()
        old_status_html = f'<span style="color: {old_color};">{old_status}</span>' if old_color else old_status
        new_status_html = f'<span style="color: {new_color};">{new_status}</span>' if new_color else new_color

        text = (f'<span style="color: {COLORS["text"]};">{author}</span> '
                f'<span style="color: {COLORS["text_secondary"]};">- {product}/{version} • </span>'
                f'{old_status_html} → {new_status_html}')

        label.setText(text)
        label.setStyleSheet(f"background-color: transparent; font-size: 8pt;")
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        layout.addWidget(label, 1)

        time_label = QLabel(f' • {timestamp}')
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        time_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        layout.addWidget(time_label, 0)

        container = QWidget()
        container.setLayout(layout)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        container.setMaximumHeight(20)
        self.main_layout.addWidget(container)

    def add_comment(self, author, timestamp, message, tags=None, activity_index=None):
        """Add comment with header outside card, message with inline tags inside card."""
        comment_container = QWidget()
        comment_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        container_layout = QVBoxLayout(comment_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(1)

        header_container = QWidget()
        header_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        header_container.setMaximumHeight(15)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(3)

        author_label = QLabel(author)
        author_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; font-size: 8pt;")
        author_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        author_label.setWordWrap(False)
        header_layout.addWidget(author_label, 1)

        time_label = QLabel(f' • {timestamp}')
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        time_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        header_layout.addWidget(time_label, 0)

        container_layout.addWidget(header_container)

        card = CommentCard(message, activity_index=activity_index)
        container_layout.addWidget(card)

        self.main_layout.addWidget(comment_container)

        if activity_index is not None:
            self._comment_cards[activity_index] = card

        return card

    def add_thumbnail_to_comment(self, activity_index, pixmap, tooltip="", file_id="", filename=""):
        """Add thumbnail with filename to comment card."""
        if activity_index in self._comment_cards:
            card = self._comment_cards[activity_index]
            thumb_label = card.add_thumbnail(pixmap, tooltip, file_id, filename)
            thumb_label.clicked.connect(self.thumbnail_clicked.emit)
            return thumb_label
        return None

    def scroll_to_bottom(self):
        """Scroll to bottom."""
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def add_version_publish(self, author, product, version, timestamp):
        """Add version publish row."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        label = QLabel()
        text = (f'<span style="color: {COLORS["text"]};">{author}</span> '
                f'<span style="color: {COLORS["text_secondary"]};">published a version</span> '
                f'<span style="color: #5b9dd9;">{product}/{version}</span>')

        label.setText(text)
        label.setStyleSheet(f"background-color: transparent; font-size: 8pt;")
        label.setTextFormat(Qt.RichText)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(label, 1)

        time_label = QLabel(f' • {timestamp}')
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        time_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        layout.addWidget(time_label, 0)

        container = QWidget()
        container.setLayout(layout)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        container.setMaximumHeight(20)
        self.main_layout.addWidget(container)

    def add_checklist(self, author, timestamp, checklist_items, activity_index=None, activity_id=None, body=None):
        """Add checklist comment with checkboxes."""
        comment_container = QWidget()
        comment_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        container_layout = QVBoxLayout(comment_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(1)

        header_container = QWidget()
        header_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        header_container.setMaximumHeight(15)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(3)

        author_label = QLabel(author)
        author_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; font-size: 8pt;")
        author_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        author_label.setWordWrap(False)
        header_layout.addWidget(author_label, 1)

        time_label = QLabel(f' • {timestamp}')
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 8pt;")
        time_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        header_layout.addWidget(time_label, 0)

        container_layout.addWidget(header_container)

        card = QFrame()
        card.setObjectName("ChecklistCard")
        card.setStyleSheet(f"""
            #ChecklistCard {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(9, 9, 9, 9)
        card_layout.setSpacing(5)

        for idx, (checked, text) in enumerate(checklist_items):
            checkbox = QCheckBox(text)
            checkbox.setChecked(checked)
            checkbox.setStyleSheet(f"color: {COLORS['text']}; font-size: 10pt;")
            if activity_id and body:
                checkbox.stateChanged.connect(
                    lambda state, aid=activity_id, b=body, i=idx: self._on_checkbox_changed(aid, b, i, state)
                )
            card_layout.addWidget(checkbox)

        container_layout.addWidget(card)
        self.main_layout.addWidget(comment_container)

    def _on_checkbox_changed(self, activity_id, body, item_index, state):
        """Handle checkbox state change."""
        self.checkbox_changed.emit(activity_id, body, item_index, state)
