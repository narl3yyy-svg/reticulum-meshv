"""Basic messaging tab using Reticulum."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
import RNS


class MessagesWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = backend.rns_node
        self.received_messages = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Messages (Reticulum)")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        info = QLabel("Send text messages to other Reticulum nodes using the same network as file transfers.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Send section
        send_group = QGroupBox("Send Message")
        send_layout = QVBoxLayout()

        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Destination Hash:"))
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Paste recipient's full 64-char identity hash")
        dest_layout.addWidget(self.dest_input)
        send_layout.addLayout(dest_layout)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setMaximumHeight(80)
        send_layout.addWidget(self.message_input)

        send_btn = QPushButton("Send Message")
        send_btn.clicked.connect(self._send_message)
        send_layout.addWidget(send_btn)

        send_group.setLayout(send_layout)
        layout.addWidget(send_group)

        # Received messages
        recv_group = QGroupBox("Received Messages")
        recv_layout = QVBoxLayout()

        self.messages_display = QTextEdit()
        self.messages_display.setReadOnly(True)
        recv_layout.addWidget(self.messages_display)

        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(lambda: self.messages_display.clear())
        recv_layout.addWidget(clear_btn)

        recv_group.setLayout(recv_layout)
        layout.addWidget(recv_group)

    def _send_message(self):
        dest_hash = self.dest_input.text().strip().lower()
        message = self.message_input.toPlainText().strip()

        if not dest_hash or len(dest_hash) != 64:
            QMessageBox.warning(self, "Error", "Please enter a valid 64-character destination hash.")
            return

        if not message:
            QMessageBox.warning(self, "Error", "Message cannot be empty.")
            return

        if not self.rns_node or not self.rns_node.identity:
            QMessageBox.warning(self, "Error", "Reticulum not ready.")
            return

        try:
            dest_hash_bytes = bytes.fromhex(dest_hash)

            remote_identity = RNS.Identity.recall(dest_hash_bytes)
            if remote_identity:
                destination = RNS.Destination(remote_identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
            else:
                destination = RNS.Destination(self.rns_node.identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
                destination.hash = dest_hash_bytes

            data = message.encode("utf-8")
            RNS.Resource(data, destination)

            self.messages_display.append(f"[You] {message}")
            self.message_input.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send message: {str(e)}")

    def add_received_message(self, sender_hash: str, message: str):
        self.messages_display.append(f"[{sender_hash[:12]}...] {message}")
