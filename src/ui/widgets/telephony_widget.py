"""LXST Telephony (voice calls) widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QGroupBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer


class TelephonyWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.telephony = backend.telephony_manager
        self.rns_node = backend.rns_node

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Telephony (LXST)")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        status_group = QGroupBox("Call Status")
        status_layout = QVBoxLayout()

        self.state_label = QLabel("Idle")
        self.state_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #888;")
        status_layout.addWidget(self.state_label)

        self.peer_label = QLabel("")
        self.peer_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        status_layout.addWidget(self.peer_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        call_group = QGroupBox("Make a Call")
        call_layout = QVBoxLayout()

        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel("Destination:"))
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("64-char identity hash")
        dest_row.addWidget(self.dest_input, 1)
        call_layout.addLayout(dest_row)

        btn_row = QHBoxLayout()
        self.call_btn = QPushButton("Call")
        self.call_btn.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
        self.call_btn.clicked.connect(self._call)
        btn_row.addWidget(self.call_btn)

        self.accept_btn = QPushButton("Accept")
        self.accept_btn.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
        self.accept_btn.clicked.connect(self._accept)
        self.accept_btn.setVisible(False)
        btn_row.addWidget(self.accept_btn)

        self.reject_btn = QPushButton("Reject")
        self.reject_btn.setStyleSheet("background-color: #FF9800;")
        self.reject_btn.clicked.connect(self._reject)
        self.reject_btn.setVisible(False)
        btn_row.addWidget(self.reject_btn)

        self.end_btn = QPushButton("End Call")
        self.end_btn.setStyleSheet("background-color: #f44336; font-weight: bold;")
        self.end_btn.clicked.connect(self._end_call)
        self.end_btn.setVisible(False)
        btn_row.addWidget(self.end_btn)

        call_layout.addLayout(btn_row)
        call_group.setLayout(call_layout)
        layout.addWidget(call_group)

        history_group = QGroupBox("Call History")
        history_layout = QVBoxLayout()

        self.history_list = QListWidget()
        history_layout.addWidget(self.history_list)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        if self.telephony:
            self.telephony.on_state_change(self._on_state_change)
            self.telephony.on_ringtone(self._on_ringtone)

        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh_history)
        self.timer.start(5000)

        self._refresh_history()

    def _on_state_change(self, state, call_info):
        if state == "idle":
            self.state_label.setText("Idle")
            self.state_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #888;")
            self.peer_label.setText("")
            self.call_btn.setVisible(True)
            self.accept_btn.setVisible(False)
            self.reject_btn.setVisible(False)
            self.end_btn.setVisible(False)
        elif state == "ringing":
            self.state_label.setText("📞 Incoming Call...")
            self.state_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FF9800;")
            if call_info:
                self.peer_label.setText(f"From: {call_info.get('peer_hash', '')[:16]}...")
            self.call_btn.setVisible(False)
            self.accept_btn.setVisible(True)
            self.reject_btn.setVisible(True)
            self.end_btn.setVisible(False)
        elif state == "connecting":
            self.state_label.setText("Connecting...")
            self.state_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
            self.call_btn.setVisible(False)
            self.accept_btn.setVisible(False)
            self.reject_btn.setVisible(False)
            self.end_btn.setVisible(True)
        elif state == "active":
            self.state_label.setText("🔴 Call Active")
            self.state_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
            self.call_btn.setVisible(False)
            self.accept_btn.setVisible(False)
            self.reject_btn.setVisible(False)
            self.end_btn.setVisible(True)

    def _on_ringtone(self, caller_hash):
        self.state_label.setText("📞 Incoming Call!")
        self.peer_label.setText(f"From: {caller_hash[:16]}...")

    def _call(self):
        dest = self.dest_input.text().strip().lower()
        if len(dest) != 64:
            QMessageBox.warning(self, "Invalid", "Enter a valid 64-char identity hash.")
            return
        if self.telephony:
            self.telephony.initiate_call(dest)

    def _accept(self):
        if self.telephony:
            self.telephony.accept_call()

    def _reject(self):
        if self.telephony:
            self.telephony.reject_call()

    def _end_call(self):
        if self.telephony:
            self.telephony.end_call()

    def _refresh_history(self):
        self.history_list.clear()
        if not self.telephony:
            return
        for call in self.telephony.get_call_history():
            peer = call.get("peer_hash", "")[:16]
            direction = "→ Outgoing" if call.get("direction") == "outgoing" else "← Incoming"
            duration = call.get("duration", 0)
            self.history_list.addItem(f"{direction} {peer}... ({duration:.0f}s)")
