"""Telephone tab — LXST voice calls to contacts."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from src.config.theme import MeshTheme
from src.ui.widgets.common import EmptyState


class TelephoneWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.lxmf_messenger = getattr(backend, 'lxmf_messenger', None)
        self.contact_manager = getattr(backend, 'contact_manager', None)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Telephone")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {MeshTheme.TEXT}; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel("Make voice calls over Reticulum using LXST.")
        subtitle.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 13px; background: transparent;")
        layout.addWidget(subtitle)

        def group_style():
            return f"""
                QGroupBox {{ color: {MeshTheme.TEXT_MUTED}; font-size: 12px;
                    border: 1px solid {MeshTheme.BORDER_CARD}; border-radius: 16px; margin-top: 20px;
                    padding: 16px; }}
                QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
                    padding: 4px 12px; color: {MeshTheme.TEXT_MUTED}; font-size: 12px; }}
            """

        # === Make a Call ===
        call_group = QGroupBox("Make a Call")
        call_group.setStyleSheet(group_style())
        call_layout = QVBoxLayout()

        call_desc = QLabel("Enter a destination hash or select a contact to call:")
        call_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        call_layout.addWidget(call_desc)

        call_row = QHBoxLayout()
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Destination hash...")
        self.dest_input.setStyleSheet(f"""
            QLineEdit {{ background-color: {MeshTheme.INPUT_BG}; color: {MeshTheme.TEXT};
                border: 1px solid {MeshTheme.INPUT_BORDER}; border-radius: 12px; padding: 10px 14px; font-size: 13px; }}
            QLineEdit:focus {{ border: 2px solid {MeshTheme.FOCUS}; }}
        """)
        call_row.addWidget(self.dest_input, 1)

        call_btn = QPushButton("Call")
        call_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.SUCCESS}; color: white; border: none;
                border-radius: 12px; padding: 10px 24px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background-color: #22c55e; }}
        """)
        call_btn.clicked.connect(self._make_call)
        call_row.addWidget(call_btn)

        call_layout.addLayout(call_row)
        call_group.setLayout(call_layout)
        layout.addWidget(call_group)

        # === Contacts ===
        contacts_group = QGroupBox("Contacts")
        contacts_group.setStyleSheet(group_style())
        contacts_layout = QVBoxLayout()

        contacts_desc = QLabel("Click a contact to start a call:")
        contacts_desc.setStyleSheet(f"color: {MeshTheme.TEXT_MUTED}; font-size: 12px; background: transparent;")
        contacts_layout.addWidget(contacts_desc)

        if self.contact_manager:
            contacts = self.contact_manager.get_all()
            if contacts:
                for c in contacts:
                    row = QHBoxLayout()
                    name_label = QLabel(c.name)
                    name_label.setStyleSheet(f"color: {MeshTheme.TEXT}; font-weight: 600; background: transparent;")
                    row.addWidget(name_label)

                    hash_label = QLabel(c.hash_hex[:16] + "...")
                    hash_label.setStyleSheet(f"font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {MeshTheme.TEXT_MUTED}; background: transparent;")
                    row.addWidget(hash_label, 1)

                    dial_btn = QPushButton("Dial")
                    dial_btn.setStyleSheet(f"""
                        QPushButton {{ background-color: {MeshTheme.SUCCESS}; color: white; border: none;
                            border-radius: 8px; padding: 6px 16px; font-size: 12px; font-weight: 600; }}
                        QPushButton:hover {{ background-color: #22c55e; }}
                    """)
                    dial_btn.clicked.connect(lambda checked, h=c.hash_hex, n=c.name: self._dial_contact(h, n))
                    row.addWidget(dial_btn)

                    contacts_layout.addLayout(row)
            else:
                no_contacts = QLabel("No contacts yet. Discover peers from the Announces tab.")
                no_contacts.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 12px; background: transparent; padding: 8px;")
                contacts_layout.addWidget(no_contacts)
        else:
            no_contacts = QLabel("Contact manager not available.")
            no_contacts.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 12px; background: transparent; padding: 8px;")
            contacts_layout.addWidget(no_contacts)

        contacts_group.setLayout(contacts_layout)
        layout.addWidget(contacts_group, 1)

        # === Status ===
        self.status_label = QLabel("No active calls")
        self.status_label.setStyleSheet(f"color: {MeshTheme.TEXT_DIM}; font-size: 13px; background: transparent; padding: 8px;")
        layout.addWidget(self.status_label)

    def _make_call(self):
        dest = self.dest_input.text().strip()
        if not dest:
            return
        self._dial_contact(dest, dest[:16])

    def _dial_contact(self, hash_str, name):
        self.dest_input.setText(hash_str)
        self.status_label.setText(f"Calling {name} ({hash_str[:16]}...)...")
        self.status_label.setStyleSheet(f"color: {MeshTheme.WARNING}; font-size: 13px; background: transparent; padding: 8px;")
        QMessageBox.information(self, "Call", f"Initiating call to {name}...\n\nLXST call functionality requires audio hardware setup.\nThis is a placeholder for future LXST integration.")
