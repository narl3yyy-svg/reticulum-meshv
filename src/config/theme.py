"""MeshChatX-inspired modern dark theme for PyQt6."""

from PyQt6.QtGui import QFont, QColor


class MeshTheme:
    CANVAS = '#0a0a0a'
    SURFACE = '#161616'
    SURFACE_VARIANT = '#1e1e1e'
    SURFACE_LIGHT = '#2a2a2a'
    TEXT = '#e8e8e8'
    TEXT_MUTED = '#9e9e9e'
    TEXT_DIM = '#6b6b6b'
    ACCENT = '#3b82f6'
    ACCENT_DARK = '#2563eb'
    ACCENT_LIGHT = '#60a5fa'
    ERROR = '#ef4444'
    SUCCESS = '#22c55e'
    WARNING = '#f59e0b'
    BORDER = '#2a2a2a'
    BORDER_LIGHT = '#3a3a3a'
    CHAT_SENT_BG = '#1a3a5c'
    CHAT_SENT_GRADIENT_1 = '#1e40af'
    CHAT_SENT_GRADIENT_2 = '#1d4ed8'
    CHAT_RECEIVED_BG = '#1e1e1e'
    CHAT_RECEIVED_BORDER = '#333333'
    SIDEBAR_BG = '#0d0d0d'
    SIDEBAR_HOVER = '#1a1a1a'
    SIDEBAR_SELECTED = '#3b82f6'
    INPUT_BG = '#141414'
    INPUT_BORDER = '#333333'
    BADGE_BG = '#3b82f6'
    BADGE_TEXT = '#ffffff'
    LINK = '#60a5fa'
    HEADING = '#f0f0f0'
    MUTED_HEADING = '#7a7a7a'


def get_stylesheet() -> str:
    t = MeshTheme
    return f"""
    QMainWindow, QWidget {{
        background-color: {t.CANVAS};
        color: {t.TEXT};
        font-family: 'Segoe UI', 'Noto Sans', -apple-system, sans-serif;
    }}
    QLabel {{
        color: {t.TEXT};
        background: transparent;
    }}
    QLineEdit {{
        background-color: {t.INPUT_BG};
        color: {t.TEXT};
        border: 1px solid {t.INPUT_BORDER};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 2px solid {t.ACCENT};
        padding: 7px 11px;
    }}
    QLineEdit::placeholder {{
        color: {t.TEXT_DIM};
    }}
    QPushButton {{
        background-color: {t.ACCENT};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {t.ACCENT_DARK};
    }}
    QPushButton:pressed {{
        background-color: {t.ACCENT_DARK};
    }}
    QPushButton:disabled {{
        background-color: {t.SURFACE_LIGHT};
        color: {t.TEXT_DIM};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t.SURFACE_LIGHT};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t.TEXT_DIM};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    QListWidget::item {{
        border-radius: 6px;
        padding: 8px 12px;
        margin: 1px 4px;
        color: {t.TEXT_MUTED};
    }}
    QListWidget::item:hover {{
        background-color: {t.SIDEBAR_HOVER};
        color: {t.TEXT};
    }}
    QListWidget::item:selected {{
        background-color: {t.SIDEBAR_SELECTED};
        color: white;
    }}
    QTreeWidget {{
        background-color: transparent;
        border: 1px solid {t.BORDER};
        border-radius: 6px;
        outline: none;
    }}
    QTreeWidget::item {{
        padding: 4px 8px;
        border-radius: 4px;
    }}
    QTreeWidget::item:hover {{
        background-color: {t.SURFACE_VARIANT};
    }}
    QHeaderView::section {{
        background-color: {t.SURFACE};
        color: {t.TEXT_MUTED};
        border: none;
        border-bottom: 1px solid {t.BORDER};
        padding: 6px 8px;
        font-weight: 600;
        font-size: 12px;
    }}
    QGroupBox {{
        border: 1px solid {t.BORDER};
        border-radius: 8px;
        margin-top: 18px;
        padding: 14px 14px 14px 14px;
        font-size: 13px;
        font-weight: 600;
        color: {t.TEXT};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 10px;
        color: {t.TEXT_MUTED};
        font-size: 11px;
        font-weight: 400;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}
    QTextEdit {{
        background-color: {t.INPUT_BG};
        color: {t.TEXT};
        border: 1px solid {t.INPUT_BORDER};
        border-radius: 6px;
        padding: 8px;
        font-size: 13px;
    }}
    QTextEdit:focus {{
        border: 2px solid {t.ACCENT};
    }}
    QProgressBar {{
        background-color: {t.SURFACE_VARIANT};
        border: none;
        border-radius: 4px;
        height: 6px;
        text-align: center;
        font-size: 10px;
    }}
    QProgressBar::chunk {{
        background-color: {t.SUCCESS};
        border-radius: 4px;
    }}
    QTableWidget {{
        background-color: transparent;
        border: 1px solid {t.BORDER};
        border-radius: 6px;
        gridline-color: {t.BORDER};
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        color: {t.TEXT};
    }}
    QTableWidget::item:selected {{
        background-color: {t.ACCENT};
        color: white;
    }}
    QSplitter::handle {{
        background-color: {t.BORDER};
        width: 1px;
    }}
    QStatusBar {{
        background-color: {t.SURFACE};
        border-top: 1px solid {t.BORDER};
        color: {t.TEXT_MUTED};
        font-size: 12px;
    }}
    QMenu {{
        background-color: {t.SURFACE};
        border: 1px solid {t.BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px;
        border-radius: 4px;
        font-size: 13px;
    }}
    QMenu::item:selected {{
        background-color: {t.ACCENT};
        color: white;
    }}
    QMenu::separator {{
        height: 1px;
        background: {t.BORDER};
        margin: 4px 8px;
    }}
    QComboBox {{
        background-color: {t.INPUT_BG};
        color: {t.TEXT};
        border: 1px solid {t.INPUT_BORDER};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
    }}
    QComboBox:focus {{
        border: 2px solid {t.ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox::item:selected {{
        background-color: {t.ACCENT};
        color: white;
    }}
    QCheckBox {{
        color: {t.TEXT};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 3px;
        border: 1px solid {t.BORDER_LIGHT};
        background: {t.INPUT_BG};
    }}
    QCheckBox::indicator:checked {{
        background: {t.ACCENT};
        border: 1px solid {t.ACCENT};
    }}
    """


def get_font(style: str) -> QFont:
    configs = {
        'title': (22, QFont.Weight.Bold),
        'headline': (18, QFont.Weight.Bold),
        'body': (14, QFont.Weight.Normal),
        'small': (11, QFont.Weight.Normal),
        'mono': (13, QFont.Weight.Normal),
    }
    size, weight = configs.get(style, configs['body'])
    font = QFont()
    font.setPointSize(size)
    font.setWeight(weight)
    if style == 'mono':
        font.setFamily('JetBrains Mono, Fira Code, Consolas, monospace')
    return font
