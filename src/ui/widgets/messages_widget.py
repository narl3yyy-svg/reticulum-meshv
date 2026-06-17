"""Messages tab placeholder (LXMF coming later)."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class MessagesWidget(QWidget):
    """Basic messages placeholder."""
    
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Messages (LXMF)")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        info = QLabel(
            "LXMF messaging will be added here soon.\n\n"
            "This will allow sending encrypted messages over the Reticulum mesh,"
            " similar to MeshChatX."
        )
        info.setWordWrap(True)
        
        layout.addWidget(title)
        layout.addWidget(info)
        layout.addStretch()
