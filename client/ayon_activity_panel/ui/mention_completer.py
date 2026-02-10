"""User mention autocomplete for comment text box."""

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QListWidget, QTextEdit
from qtpy.QtGui import QTextCursor
from ..api.ayon.base_client import BaseAyonClient


class MentionCompleter(QListWidget):
    """Popup list for @ mention autocomplete."""

    mention_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMaximumHeight(150)
        self.itemClicked.connect(self._on_item_clicked)
        self.users = []

    def _on_item_clicked(self, item):
        self.mention_selected.emit(item.text())
        self.hide()

    def show_suggestions(self, users, filter_text=''):
        """Show filtered user suggestions."""
        self.clear()
        filtered = [u for u in users if filter_text.lower() in u.lower()]
        if filtered:
            self.addItems(filtered)
            self.setCurrentRow(0)
            self.show()
        else:
            self.hide()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.currentItem():
                self.mention_selected.emit(self.currentItem().text())
                self.hide()
        elif event.key() in (Qt.Key_Escape, Qt.Key_Space):
            self.hide()
        else:
            super().keyPressEvent(event)


class CommentTextEdit(QTextEdit):
    """QTextEdit with @ mention autocomplete."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.completer = MentionCompleter(self)
        self.completer.mention_selected.connect(self._insert_mention)
        self.users = []
        self.mention_start = -1

    def fetch_users(self, project_name):
        """Fetch users from AYON."""
        query = """
        query {
            users {
                edges {
                    node {
                        name
                    }
                }
            }
        }
        """
        try:
            result = BaseAyonClient.graphql_query(query, {})
            self.users = [edge['node']['name'] for edge in result['data']['users']['edges']]
        except:
            self.users = []

    def keyPressEvent(self, event):
        if self.completer.isVisible():
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape, Qt.Key_Space, Qt.Key_Up, Qt.Key_Down):
                self.completer.keyPressEvent(event)
                if event.key() == Qt.Key_Space:
                    self.mention_start = -1
                return

        # Check for @ mention BEFORE processing the key
        cursor = self.textCursor()
        pos_before = cursor.position()

        if event.text() == '@':
            self.mention_start = pos_before

        super().keyPressEvent(event)

        cursor = self.textCursor()
        text = self.toPlainText()
        pos = cursor.position()

        # Show completer after @ is inserted
        if event.text() == '@':
            self._show_completer('')
        elif self.mention_start >= 0:
            mention_text = text[self.mention_start:pos]
            if ' ' in mention_text or '\n' in mention_text:
                self.mention_start = -1
                self.completer.hide()
            else:
                filter_text = mention_text.lstrip('@')
                self._show_completer(filter_text)

    def _show_completer(self, filter_text):
        """Show completer popup."""
        if not self.users:
            return

        cursor = self.textCursor()
        cursor_rect = self.cursorRect(cursor)
        popup_pos = self.mapToGlobal(cursor_rect.bottomLeft())

        self.completer.move(popup_pos)
        self.completer.setFixedWidth(200)
        self.completer.show_suggestions(self.users, filter_text)

    def _insert_mention(self, username):
        """Insert selected mention."""
        cursor = self.textCursor()
        text = self.toPlainText()

        # Calculate how much text to remove (from @ to current position)
        current_pos = cursor.position()
        chars_to_remove = current_pos - self.mention_start

        # Move cursor to mention start and select all typed text
        cursor.setPosition(self.mention_start)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, chars_to_remove)

        # Replace with @username
        cursor.removeSelectedText()
        cursor.insertText(f"@{username} ")
        self.setTextCursor(cursor)
        self.mention_start = -1
