"""Telephone tab — LXST voice calls to contacts."""

import RNS
import LXST
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from src.config.theme import MeshTheme
from src.ui.widgets.common import EmptyState


class TelephoneWidget(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.rns_node = getattr(backend, 'rns_node', None)
        self.lxmf_messenger = getattr(backend, 'lxmf_messenger', None)
        self.contact_manager = getattr(backend, 'contact_manager', None)
        self.identity = self.rns_node.get_identity() if self.rns_node else None
        self.telephone = None
        self._call_active = False

        # Try to initialize LXST Telephone
        if self.identity:
            try:
                self.telephone = LXST.Telephone(self.identity)
                self.telephone.set_ringing_callback(self._on_ringing)
                self.telephone.set_established_callback(self._on_established)
                self.telephone.set_ended_callback(self._on_ended)
                self.telephone.set_busy_callback(self._on_busy)
                self.telephone.set_rejected_callback(self._on_rejected)
                print("[Telephone] LXST Telephone initialized")
            except Exception as e:
                print(f"[Telephone] Could not init LXST: {e}")

        self.init_ui()

        # Status refresh timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_status)
        self._timer.start(2000)

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

        self.call_btn = QPushButton("Call")
        self.call_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.SUCCESS}; color: white; border: none;
                border-radius: 12px; padding: 10px 24px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background-color: #22c55e; }}
            QPushButton:disabled {{ background-color: {MeshTheme.SURFACE_LIGHT}; color: {MeshTheme.TEXT_DIM}; }}
        """)
        self.call_btn.clicked.connect(self._make_call)
        call_row.addWidget(self.call_btn)

        self.hangup_btn = QPushButton("Hang Up")
        self.hangup_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {MeshTheme.ERROR}; color: white; border: none;
                border-radius: 12px; padding: 10px 24px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background-color: #dc2626; }}
            QPushButton:disabled {{ background-color: {MeshTheme.SURFACE_LIGHT}; color: {MeshTheme.TEXT_DIM}; }}
        """)
        self.hangup_btn.clicked.connect(self._hangup)
        self.hangup_btn.setEnabled(False)
        call_row.addWidget(self.hangup_btn)

        call_layout.addLayout(call_row)
        call_group.setLayout(call_layout)
        layout.addWidget(call_group)

        # === Call Status ===
        status_group = QGroupBox("Call Status")
        status_group.setStyleSheet(group_style())
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Available")
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.TEXT_MUTED}; background: transparent; padding: 8px;")
        status_layout.addWidget(self.status_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # === Contacts ===
        contacts_group = QGroupBox("Contacts")
        contacts_group.setStyleSheet(group_style())
        contacts_layout = QVBoxLayout()

        contacts_desc = QLabel("Click Dial to call a contact:")
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

        if not self.telephone:
            warn = QLabel("LXST Telephone not available. Voice calls require LXST with audio backend.")
            warn.setStyleSheet(f"color: {MeshTheme.WARNING}; font-size: 12px; background: transparent; padding: 8px;")
            layout.addWidget(warn)

    def _make_call(self):
        dest = self.dest_input.text().strip()
        if not dest:
            return
        self._dial_contact(dest, dest[:16])

    def _dial_contact(self, hash_str, name):
        if not self.telephone:
            QMessageBox.warning(self, "No Telephone", "LXST Telephone is not available.")
            return
        if self._call_active:
            QMessageBox.warning(self, "Busy", "A call is already active. Hang up first.")
            return

        self.dest_input.setText(hash_str)
        try:
            dest_bytes = bytes.fromhex(hash_str)
            remote_identity = RNS.Identity.recall(dest_bytes)
            if not remote_identity:
                remote_identity = RNS.Identity()
                remote_identity.hash = dest_bytes

            self.status_label.setText(f"Calling {name}...")
            self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.WARNING}; background: transparent; padding: 8px;")
            self.call_btn.setEnabled(False)
            self.hangup_btn.setEnabled(True)

            self.telephone.call(remote_identity)
            self._call_active = True
            print(f"[Telephone] Calling {name} ({hash_str[:16]}...)")
        except Exception as e:
            self.status_label.setText(f"Call failed: {e}")
            self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.ERROR}; background: transparent; padding: 8px;")
            self.call_btn.setEnabled(True)
            self.hangup_btn.setEnabled(False)

    def _hangup(self):
        if self.telephone:
            try:
                self.telephone.hangup()
            except:
                pass
        self._call_active = False
        self.call_btn.setEnabled(True)
        self.hangup_btn.setEnabled(False)
        self.status_label.setText("Available")
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.TEXT_MUTED}; background: transparent; padding: 8px;")

    def _on_ringing(self):
        self.status_label.setText("Ringing...")
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.WARNING}; background: transparent; padding: 8px;")

    def _on_established(self):
        self.status_label.setText("Call established")
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.SUCCESS}; background: transparent; padding: 8px;")

    def _on_ended(self):
        self._call_active = False
        self.call_btn.setEnabled(True)
        self.hangup_btn.setEnabled(False)
        self.status_label.setText("Call ended")
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.TEXT_MUTED}; background: transparent; padding: 8px;")

    def _on_busy(self):
        self._call_active = False
        self.call_btn.setEnabled(True)
        self.hangup_btn.setEnabled(False)
        self.status_label.setText("Busy")
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.ERROR}; background: transparent; padding: 8px;")

    def _on_rejected(self):
        self._call_active = False
        self.call_btn.setEnabled(True)
        self.hangup_btn.setEnabled(False)
        self.status_label.setText("Rejected")
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.ERROR}; background: transparent; padding: 8px;")

    def _update_status(self):
        if not self._call_active and self.telephone:
            status = getattr(self.telephone, 'call_status', None)
            if status is not None:
                try:
                    available = status == getattr(LXST.Signalling, 'STATUS_AVAILABLE', 0)
                    if available and self.status_label.text() != "Available":
                        self.status_label.setText("Available")
                        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {MeshTheme.TEXT_MUTED}; background: transparent; padding: 8px;")
                except:
                    pass
