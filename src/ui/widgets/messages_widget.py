"""MeshChatX-inspired messages widget with reliable bubble rendering."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QLabel, QLineEdit, QTextEdit, QScrollArea, QFrame, QSizePolicy,
    QApplication, QMenu
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QDateTime, QEvent
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen
from src.config.theme import MeshTheme
from src.ui.widgets.common import EmptyState


STATUS_SYMBOLS = {
    'sending': '\u23F3',
    'sent': '\u2713',
    'delivered': '\u2713\u2713',
    'read': '\u2713\u2713',
    'failed': '\u274C',
}


class ChatBubble(QFrame):
    def __init__(self, text, sender, timestamp, is_self=False, status='sent', parent=None):
        super().__init__(parent)
        self._is_self = is_self
        self._status = status
        self._sender = sender
        self._timestamp = timestamp
        t = MeshTheme

        if is_self:
            self.setStyleSheet(f"""
                ChatBubble {{
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {t.CHAT_SENT_GRADIENT_1}, stop:1 {t.CHAT_SENT_GRADIENT_2});
                    border-radius: 12px;
                    padding: 10px 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ChatBubble {{
                    background-color: {t.CHAT_RECEIVED_BG};
                    border: 1px solid {t.CHAT_RECEIVED_BORDER};
                    border-radius: 12px;
                    padding: 10px 14px;
                }}
            """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        if not is_self:
            name_label = QLabel(sender)
            name_label.setStyleSheet(f"color: {t.ACCENT}; font-size: 11px; font-weight: 600; background: transparent;")
            layout.addWidget(name_label)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_color = '#ffffff' if is_self else t.TEXT
        text_label.setStyleSheet(f"color: {text_color}; font-size: 13px; background: transparent;")
        layout.addWidget(text_label)

        meta_layout = QHBoxLayout()
        meta_layout.setContentsMargins(0, 0, 0, 0)

        time_label = QLabel(timestamp.toString('HH:mm'))
        time_color = '#ffffffb3' if is_self else t.TEXT_DIM
        time_label.setStyleSheet(f"color: {time_color}; font-size: 10px; background: transparent;")
        meta_layout.addWidget(time_label)

        if is_self:
            meta_layout.addStretch()
            status_str = STATUS_SYMBOLS.get(status, '')
            status_color = MeshTheme.SUCCESS if status == 'read' else '#ffffffb3'
            status_label = QLabel(status_str)
            status_label.setStyleSheet(f"color: {status_color}; font-size: 10px; background: transparent;")
            meta_layout.addWidget(status_label)

        layout.addLayout(meta_layout)

    def set_message(self, text):
        self.findChild(QLabel).setText(text)


class ConversationListItem(QFrame):
    selected = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, conv_id, display_name, last_message, timestamp, unread=0, parent=None):
        super().__init__(parent)
        self.conv_id = conv_id
        self._display = display_name
        self._last_msg = last_message
        self._ts = timestamp
        self._unread = unread
        self._selected = False
        self.setFixedHeight(68)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        avatar = QLabel(display_name[0].upper() if display_name else '?')
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {MeshTheme.SURFACE_LIGHT};
            color: {MeshTheme.ACCENT};
            font-size: 18px; font-weight: 700;
            border-radius: 22px;
        """)
        layout.addWidget(avatar)

        text_wrap = QVBoxLayout()
        text_wrap.setContentsMargins(0, 0, 0, 0)
        text_wrap.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        name_label = QLabel(display_name)
        name_label.setStyleSheet(f"color: {MeshTheme.TEXT}; font-size: 13px; font-weight: 600; background: transparent;")
        top_row.addWidget(name_label)
        top_row.addStretch()
        ts_label = QLabel(timestamp.toString('HH:mm') if timestamp else '')
        ts_label.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 10px; background: transparent;")
        top_row.addWidget(ts_label)
        text_wrap.addLayout(top_row)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        msg_label = QLabel(last_message[:60])
        msg_label.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        bottom_row.addWidget(msg_label, 1)
        if unread > 0:
            badge = QLabel(str(min(unread, 99)))
            badge.setFixedSize(22, 22)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"""
                background-color: {MeshTheme.ACCENT}; color: white;
                font-size: 10px; font-weight: 700; border-radius: 11px;
            """)
            bottom_row.addWidget(badge)
        text_wrap.addLayout(bottom_row)

        layout.addLayout(text_wrap, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.conv_id)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {MeshTheme.SURFACE};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 6px 20px; border-radius: 4px; color: {MeshTheme.TEXT}; }}
            QMenu::item:selected {{ background-color: {MeshTheme.ACCENT}; color: white; }}
        """)
        delete_a = menu.addAction("Delete Conversation")
        action = menu.exec(event.globalPos())
        if action == delete_a:
            self.delete_requested.emit(self.conv_id)

    def set_selected(self, sel):
        self._selected = sel
        bg = MeshTheme.SURFACE_VARIANT if sel else 'transparent'
        self.setStyleSheet(f"background-color: {bg}; border-radius: 0;")

    def update_message(self, msg, ts=None):
        self._last_msg = msg
        if ts:
            self._ts = ts
        labels = self.findChildren(QLabel)
        if len(labels) >= 3:
            labels[2].setText(msg[:60])
        if ts and len(labels) >= 2:
            labels[1].setText(ts.toString('HH:mm'))
        self.update()


class MessagesWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        layout.addWidget(splitter, 1)

        self.conversation_panel = self._build_conversation_panel()
        splitter.addWidget(self.conversation_panel)
        splitter.setStretchFactor(0, 0)

        self.chat_panel = self._build_chat_panel()
        splitter.addWidget(self.chat_panel)
        splitter.setStretchFactor(1, 1)

        splitter.setSizes([320, 700])

        self.conversations = {}
        self.current_conv_id = None
        self._populate_conversations()

    def _build_conversation_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {MeshTheme.SIDEBAR_BG};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(64)
        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(16, 0, 16, 0)
        title = QLabel("Messages")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {MeshTheme.TEXT}; background: transparent;")
        hdr_layout.addWidget(title)
        hdr_layout.addStretch()
        new_btn = QPushButton("+")
        new_btn.setFixedSize(32, 32)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MeshTheme.ACCENT}; color: white; border: none;
                border-radius: 16px; font-size: 18px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT_DARK}; }}
        """)
        new_btn.clicked.connect(self._new_conversation)
        hdr_layout.addWidget(new_btn)
        layout.addWidget(header)

        search = QLineEdit()
        search.setPlaceholderText("Search conversations...")
        search.setFixedHeight(48)
        search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.BORDER}; border-radius: 10px;
                padding: 12px 16px; font-size: 15px; margin: 8px 12px;
                font-weight: 500;
            }}
            QLineEdit:focus {{ border: 2px solid {MeshTheme.ACCENT}; }}
            QLineEdit::placeholder {{ color: {MeshTheme.TEXT_MUTED}; font-size: 14px; }}
        """)
        search.textChanged.connect(self._filter_conversations)
        layout.addWidget(search)

        self.conv_empty = EmptyState("M", "No conversations", "Messages from contacts appear here")
        layout.addWidget(self.conv_empty)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.conv_list = QWidget()
        self.conv_layout = QVBoxLayout(self.conv_list)
        self.conv_layout.setContentsMargins(0, 0, 0, 0)
        self.conv_layout.setSpacing(0)
        self.conv_layout.addStretch()
        scroll.setWidget(self.conv_list)

        layout.addWidget(scroll, 1)
        return panel

    def _build_chat_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {MeshTheme.CANVAS};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.chat_header = QFrame()
        self.chat_header.setFixedHeight(64)
        self.chat_header.setStyleSheet(f"background-color: {MeshTheme.SURFACE}; border-bottom: 1px solid {MeshTheme.BORDER};")
        ch_layout = QHBoxLayout(self.chat_header)
        ch_layout.setContentsMargins(20, 0, 20, 0)
        self.chat_title = QLabel("Select a conversation")
        self.chat_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.TEXT}; background: transparent;")
        ch_layout.addWidget(self.chat_title)
        ch_layout.addStretch()
        layout.addWidget(self.chat_header)

        from PyQt6.QtWidgets import QStackedWidget
        self.chat_stack = QStackedWidget()
        self.chat_stack.setStyleSheet("background: transparent;")

        self.chat_empty = EmptyState("M", "No conversation selected", "Choose a conversation from the sidebar to start chatting")
        self.chat_stack.addWidget(self.chat_empty)

        chat_content = QWidget()
        chat_content.setStyleSheet("background: transparent;")
        chat_clayout = QVBoxLayout(chat_content)
        chat_clayout.setContentsMargins(0, 0, 0, 0)
        chat_clayout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.messages_container = QWidget()
        self.messages_container.setStyleSheet("background: transparent;")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(12, 8, 12, 8)
        self.messages_layout.setSpacing(6)
        self.messages_layout.addStretch()
        scroll.setWidget(self.messages_container)
        chat_clayout.addWidget(scroll, 1)

        input_frame = QFrame()
        input_frame.setStyleSheet(f"background-color: {MeshTheme.SURFACE}; border-top: 1px solid {MeshTheme.BORDER};")
        inp_layout = QHBoxLayout(input_frame)
        inp_layout.setContentsMargins(16, 10, 16, 10)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setFixedHeight(44)
        self.message_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.INPUT_BORDER};
                border-radius: 22px; padding: 10px 18px; font-size: 14px;
            }}
            QTextEdit:focus {{ border: 2px solid {MeshTheme.ACCENT}; }}
            QTextEdit::placeholder {{ color: {MeshTheme.TEXT_DIM}; }}
        """)
        inp_layout.addWidget(self.message_input, 1)

        attach_btn = QPushButton("+")
        attach_btn.setFixedSize(44, 44)
        attach_btn.setStyleSheet(f"""
            QPushButton {{
                background: {MeshTheme.SURFACE_LIGHT}; color: {MeshTheme.TEXT};
                border: none; border-radius: 22px;
                font-size: 22px; font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.BORDER_STRONG}; }}
        """)
        attach_btn.clicked.connect(self._attach_file)
        inp_layout.addWidget(attach_btn)

        send_btn = QPushButton(">")
        send_btn.setFixedSize(44, 44)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MeshTheme.ACCENT}; color: white; border: none;
                border-radius: 22px; font-size: 22px; font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {MeshTheme.ACCENT_DARK}; }}
        """)
        send_btn.clicked.connect(self._send_message)
        inp_layout.addWidget(send_btn)

        self.message_input.installEventFilter(self)

        chat_clayout.addWidget(input_frame)
        self.chat_stack.addWidget(chat_content)
        layout.addWidget(self.chat_stack, 1)
        self.chat_stack.setCurrentIndex(0)
        return panel

    def eventFilter(self, obj, event):
        if obj is self.message_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._send_message()
                return True
        return super().eventFilter(obj, event)

    def _populate_conversations(self):
        contacts = self.backend.contact_manager.get_all() if self.backend.contact_manager else []
        for contact in contacts[:10]:
            conv_id = contact.hash_hex
            name = contact.name or conv_id[:8]
            self.add_conversation(conv_id, name)

    def add_conversation(self, conv_id, display_name):
        if conv_id in self.conversations:
            return
        item = ConversationListItem(conv_id, display_name, "No messages yet",
                                    QDateTime.currentDateTime(), 0)
        item.selected.connect(self._select_conversation)
        item.delete_requested.connect(self._delete_conversation)
        self.conversations[conv_id] = item
        self.conv_layout.insertWidget(self.conv_layout.count() - 1, item)
        self.conv_empty.setVisible(False)

    def _select_conversation(self, conv_id):
        for cid, item in self.conversations.items():
            item.set_selected(cid == conv_id)
        self.current_conv_id = conv_id
        name = conv_id
        for cid, item in self.conversations.items():
            if cid == conv_id:
                name = item._display
                break
        self.chat_title.setText(name)
        self.chat_stack.setCurrentIndex(1)
        self._load_messages(conv_id)

    def _load_messages(self, conv_id):
        for i in reversed(range(self.messages_layout.count())):
            w = self.messages_layout.itemAt(i).widget()
            if w and w is not self.messages_layout.itemAt(self.messages_layout.count() - 1).widget():
                w.deleteLater()

    def _send_message(self):
        text = self.message_input.toPlainText().strip()
        if not text or not self.current_conv_id:
            return
        ts = QDateTime.currentDateTime()
        bubble = ChatBubble(text, "me", ts, True, 'sent')
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble, 0, Qt.AlignmentFlag.AlignRight)
        self.message_input.clear()
        conv = self.conversations.get(self.current_conv_id)
        if conv:
            conv.update_message(text, ts)
        if self.backend and hasattr(self.backend, 'send_message'):
            self.backend.send_message(self.current_conv_id, text)

    def _filter_conversations(self, text):
        for conv_id, item in self.conversations.items():
            item.setVisible(text.lower() in item._display.lower())

    def _delete_conversation(self, conv_id):
        item = self.conversations.pop(conv_id, None)
        if item:
            self.conv_layout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        if self.current_conv_id == conv_id:
            self.current_conv_id = None
            self.chat_title.setText("Select a conversation")
            self.chat_stack.setCurrentIndex(0)
            self._load_messages(conv_id)
        self.conv_empty.setVisible(len(self.conversations) == 0)

    def _new_conversation(self):
        from PyQt6.QtWidgets import QInputDialog
        dialog = QInputDialog(self)
        dialog.setWindowTitle("New Conversation")
        dialog.setLabelText("Enter destination hash:")
        if dialog.exec():
            dest = dialog.textValue().strip()
            if dest:
                self.add_conversation(dest, dest[:16])
                self._select_conversation(dest)

    def _attach_file(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Attach File")
        if path:
            import os
            fname = os.path.basename(path)
            size = os.path.getsize(path)
            size_str = self._format_file_size(size)
            self._add_file_bubble(fname, size_str, path)

    def _format_file_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"

    def _add_file_bubble(self, fname, size_str, path=""):
        bubble = QFrame()
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {MeshTheme.SURFACE};
                border: 1px solid {MeshTheme.BORDER_CARD};
                border-radius: 12px;
                padding: 10px 14px;
            }}
        """)
        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(4)

        file_row = QHBoxLayout()
        file_row.setContentsMargins(0, 0, 0, 0)
        file_row.setSpacing(10)

        icon = QLabel("[FILE]")
        icon.setStyleSheet(f"color: {MeshTheme.ACCENT}; font-size: 11px; font-weight: 700; background: transparent; padding: 4px 8px; border: 1px solid {MeshTheme.BORDER}; border-radius: 6px;")
        file_row.addWidget(icon)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(2)
        name_label = QLabel(fname)
        name_label.setStyleSheet(f"color: {MeshTheme.TEXT}; font-size: 13px; font-weight: 600; background: transparent;")
        info.addWidget(name_label)
        size_label = QLabel(size_str)
        size_label.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 11px; background: transparent;")
        info.addWidget(size_label)
        file_row.addLayout(info, 1)
        bl.addLayout(file_row)

        ts = QDateTime.currentDateTime()
        time_label = QLabel(ts.toString('HH:mm'))
        time_label.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 10px; background: transparent;")
        bl.addWidget(time_label)

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble, 0, Qt.AlignmentFlag.AlignRight)

        conv = self.conversations.get(self.current_conv_id)
        if conv:
            conv.update_message(f"[File] {fname}", ts)

        if self.backend and hasattr(self.backend, 'send_message') and self.current_conv_id and path:
            try:
                self.backend.send_message(self.current_conv_id, f"[File: {fname} ({size_str})]")
            except:
                pass

    def _add_system_message(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"font-size: 11px; color: {MeshTheme.TEXT_DIM}; background: transparent; padding: 4px;")
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, label)

    def receive_text_message(self, sender_hash: str, text: str):
        if self.backend and hasattr(self.backend, 'is_sender_allowed'):
            if not self.backend.is_sender_allowed(sender_hash):
                return
        if sender_hash not in self.conversations:
            self.add_conversation(sender_hash, sender_hash[:16])
        ts = QDateTime.currentDateTime()
        bubble = ChatBubble(text, sender_hash, ts, False, 'received')
        if self.current_conv_id == sender_hash:
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble, 0, Qt.AlignmentFlag.AlignLeft)
        conv = self.conversations.get(sender_hash)
        if conv:
            conv.update_message(text, ts)

    def receive_lxmf_message(self, sender_hash: str, content: str, title: str, timestamp: float):
        if self.backend and hasattr(self.backend, 'is_sender_allowed'):
            if not self.backend.is_sender_allowed(sender_hash):
                return
        if sender_hash not in self.conversations:
            name = sender_hash[:16]
            if self.backend.contact_manager:
                contact = self.backend.contact_manager.get(sender_hash)
                if contact:
                    name = contact.name
            self.add_conversation(sender_hash, name)
        ts = QDateTime.fromSecsSinceEpoch(int(timestamp)) if timestamp else QDateTime.currentDateTime()
        bubble = ChatBubble(content, sender_hash, ts, False, 'received')
        if self.current_conv_id == sender_hash:
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble, 0, Qt.AlignmentFlag.AlignLeft)
        conv = self.conversations.get(sender_hash)
        if conv:
            conv.update_message(content[:60], ts)

    def statusBar(self):
        p = self.parent()
        while p:
            if hasattr(p, 'statusBar'):
                return p.statusBar()
            p = p.parent()
        return None
