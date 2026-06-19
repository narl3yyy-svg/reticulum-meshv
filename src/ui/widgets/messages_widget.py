"""Enhanced Messages widget with LXMF support and conversation management."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMessageBox, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime


class ChatBubble(QFrame):
    def __init__(self, text: str, is_sent: bool = True, timestamp: str = "", sender_label: str = ""):
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

        if sender_label and not is_sent:
            sender = QLabel(sender_label)
            sender.setStyleSheet("font-size: 10px; color: #8888ff; font-weight: bold;")
            layout.addWidget(sender)

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
        self.lxmf = backend.lxmf_messenger
        self.current_dest = ""
        self.current_conv = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel("Messages")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search contacts...")
        self.search_input.textChanged.connect(self._filter_conversations)
        search_row.addWidget(self.search_input)
        left_layout.addLayout(search_row)

        self.conv_list = QListWidget()
        self.conv_list.itemClicked.connect(self._on_conv_selected)
        left_layout.addWidget(self.conv_list)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 0, 0, 0)

        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel("To:"))
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("64-char destination hash")
        self.dest_input.setMinimumHeight(28)
        dest_row.addWidget(self.dest_input, 1)

        start_btn = QPushButton("Start Chat")
        start_btn.setMinimumHeight(28)
        start_btn.clicked.connect(self._start_chat)
        dest_row.addWidget(start_btn)

        announce_btn = QPushButton("Announce")
        announce_btn.setMinimumHeight(28)
        announce_btn.clicked.connect(self._announce)
        dest_row.addWidget(announce_btn)

        right_layout.addLayout(dest_row)

        self.status_label = QLabel("Enter a destination hash and click Start Chat")
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        right_layout.addWidget(self.status_label)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("QScrollArea { border: none; }")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(6)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        right_layout.addWidget(self.chat_scroll, 1)

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

        right_layout.addLayout(input_row)

        splitter.addWidget(right_panel)
        splitter.setSizes([200, 800])
        layout.addWidget(splitter, 1)

        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._scroll_to_bottom)

        self._refresh_conversations()

    def _announce(self):
        if self.lxmf:
            self.lxmf.announce()
            self.status_label.setText("Announced on LXMF network")
        elif self.rns_node:
            self.rns_node.announce_myself()
            self.status_label.setText("Announced on Reticulum network")

    def _start_chat(self):
        dest = self.dest_input.text().strip().lower().replace(" ", "").replace("-", "")
        if len(dest) == 64:
            self.current_dest = dest
            self.current_conv = []
            self._clear_chat()
            self.status_label.setText(f"Chat active with {dest[:12]}...")
            self._add_system_message(f"Started chat with {dest[:12]}...")

            if self.lxmf:
                self.current_conv = self.lxmf.get_conversation(dest)
                for msg in self.current_conv:
                    is_sent = msg.get("is_outgoing", False) or msg.get("sender", "") == self.rns_node.get_identity_hash()
                    self._add_bubble(msg["content"], is_sent=is_sent, timestamp=self._fmt_time(msg.get("timestamp", 0)))
        else:
            self.status_label.setText("Hash must be exactly 64 hex characters.")

    def _send_message(self):
        if not self.current_dest:
            self.status_label.setText("Start a chat first")
            return

        text = self.message_input.text().strip()
        if not text:
            return

        self._add_bubble(text, is_sent=True)
        self.message_input.clear()

        sent = False
        if self.lxmf:
            sent = self.lxmf.send_message(self.current_dest, text)

        if not sent and self.rns_node:
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
                sent = True
            except:
                pass

        if sent:
            self.status_label.setText("Message sent")
        else:
            self.status_label.setText("Send failed")

    def _on_conv_selected(self, item):
        hash_hex = item.data(Qt.ItemDataRole.UserRole)
        if hash_hex:
            self.dest_input.setText(hash_hex)
            self._start_chat()

    def _filter_conversations(self):
        self._refresh_conversations()

    def _refresh_conversations(self):
        self.conv_list.clear()
        query = self.search_input.text().strip().lower()

        contacts = self.backend.contact_manager.get_all() if self.backend.contact_manager else []
        seen = set()
        for c in contacts:
            if query and query not in c.name.lower() and query not in c.hash_hex.lower():
                continue
            item = QListWidgetItem(f"{c.name}")
            item.setData(Qt.ItemDataRole.UserRole, c.hash_hex)
            item.setData(Qt.ItemDataRole.ToolTipRole, c.hash_hex)
            self.conv_list.addItem(item)
            seen.add(c.hash_hex)

        if self.lxmf:
            for conv_id, msgs in self.lxmf.get_conversations().items():
                if conv_id in seen:
                    continue
                if query and query not in conv_id[:12]:
                    continue
                item = QListWidgetItem(f"{conv_id[:12]}...")
                item.setData(Qt.ItemDataRole.UserRole, conv_id)
                self.conv_list.addItem(item)

    def receive_text_message(self, sender_hash: str, text: str):
        short = sender_hash[:12] if len(sender_hash) > 12 else sender_hash
        self._add_bubble(f"[{short}] {text}", is_sent=False)

    def receive_lxmf_message(self, sender_hash: str, content: str, title: str, timestamp: float):
        if sender_hash == self.current_dest:
            self._add_bubble(content, is_sent=False, timestamp=self._fmt_time(timestamp))
        self._refresh_conversations()

    def _add_system_message(self, text: str):
        label = QLabel(f"• {text}")
        label.setStyleSheet("color: #888; font-style: italic; padding: 4px 8px;")
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, label)
        self._scroll_to_bottom()

    def _add_bubble(self, text: str, is_sent: bool = True, timestamp: str = ""):
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")
        bubble = ChatBubble(text, is_sent=is_sent, timestamp=timestamp)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _clear_chat(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _fmt_time(self, ts: float) -> str:
        if ts:
            return datetime.fromtimestamp(ts).strftime("%H:%M")
        return ""

    def _scroll_to_bottom(self):
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )
