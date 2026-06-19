"""Desktop Messages widget - Improved for better mobile interoperability."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime


class ChatBubble(QFrame):
    def __init__(self, text: str, is_sent: bool = True, timestamp: str = ""):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        if is_sent:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3a7bd5;
                    border-radius: 16px;
                    padding: 10px 14px;
                    margin: 4px 8px 4px 70px;
                }
                QLabel { color: white; }
            """)
            alignment = Qt.AlignmentFlag.AlignRight
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3a3a3c;
                    border-radius: 16px;
                    padding: 10px 14px;
                    margin: 4px 70px 4px 8px;
                }
                QLabel { color: #e0e0e0; }
            """)
            alignment = Qt.AlignmentFlag.AlignLeft

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(text_label)

        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet("font-size: 10px; color: #aaaaaa;")
            time_label.setAlignment(alignment)
            layout.addWidget(time_label)


class MessagesWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = backend.rns_node
        self.current_dest = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        header = QLabel("Messages")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_row.addWidget(header)
        header_row.addStretch()

        announce_btn = QPushButton("Announce Myself")
        announce_btn.setMinimumHeight(28)
        announce_btn.clicked.connect(self._announce_myself)
        header_row.addWidget(announce_btn)
        layout.addLayout(header_row)

        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel("To:"))
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("64-char destination hash")
        self.dest_input.setMinimumHeight(32)
        dest_row.addWidget(self.dest_input, 1)

        start_btn = QPushButton("Start Chat")
        start_btn.setMinimumHeight(32)
        start_btn.clicked.connect(self._start_chat)
        dest_row.addWidget(start_btn)
        layout.addLayout(dest_row)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("QScrollArea { border: none; }")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(6)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, 1)

        input_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setMinimumHeight(36)
        self.message_input.returnPressed.connect(self._send_message)
        input_row.addWidget(self.message_input, 1)

        send_btn = QPushButton("Send")
        send_btn.setMinimumHeight(36)
        send_btn.setStyleSheet("font-weight: bold;")
        send_btn.clicked.connect(self._send_message)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._scroll_to_bottom)

    def _announce_myself(self):
        if self.rns_node and self.rns_node.announce_myself():
            QMessageBox.information(self, "Announced", "You are now visible on the network.")
        else:
            QMessageBox.warning(self, "Error", "Could not announce.")

    def _start_chat(self):
        dest = self.dest_input.text().strip().lower().replace(" ", "").replace("-", "")
        if len(dest) == 64:
            self.current_dest = dest
            self.status_label.setText(f"Chat active with {dest[:12]}...")
            self._add_system_message(f"Now chatting with {dest[:12]}...")
        else:
            self.status_label.setText("Hash must be exactly 64 characters.")

    def _send_message(self):
        if not self.current_dest:
            self.status_label.setText("Please start a chat first.")
            return

        text = self.message_input.text().strip()
        if not text:
            return

        self._add_bubble(text, is_sent=True)
        self.message_input.clear()

        try:
            import RNS
            dest_bytes = bytes.fromhex(self.current_dest)
            remote_id = RNS.Identity.recall(dest_bytes)

            if remote_id:
                destination = RNS.Destination(remote_id, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
            else:
                destination = RNS.Destination(self.rns_node.identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
                destination.hash = dest_bytes

            RNS.Resource(text.encode("utf-8"), destination)
        except Exception as e:
            self.status_label.setText(f"Send failed: {str(e)}")

    def _add_system_message(self, text: str):
        label = QLabel(f"• {text}")
        label.setStyleSheet("color: #888; font-style: italic; padding: 4px 8px;")
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, label)
        self._scroll_to_bottom()

    def _add_bubble(self, text: str, is_sent: bool = True):
        timestamp = datetime.now().strftime("%H:%M")
        bubble = ChatBubble(text, is_sent=is_sent, timestamp=timestamp)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def receive_text_message(self, sender_hash: str, text: str):
        """Called from backend when a text message arrives from another node."""
        short = sender_hash[:12] if len(sender_hash) > 12 else sender_hash
        self._add_bubble(f"[{short}] {text}", is_sent=False)

    def _scroll_to_bottom(self):
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )
