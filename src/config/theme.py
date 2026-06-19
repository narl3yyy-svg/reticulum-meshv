"""MeshChatX-inspired dark theme for PyQt6."""

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt


class MeshTheme:
    CANVAS = '#09090b'
    SURFACE = '#18181b'
    SURFACE_VARIANT = '#27272a'
    SURFACE_LIGHT = '#3f3f46'
    TEXT = '#f3f4f6'
    TEXT_MUTED = '#a1a1aa'
    TEXT_DIM = '#71717a'
    ACCENT = '#60a5fa'
    ACCENT_DARK = '#3b82f6'
    ERROR = '#f87171'
    SUCCESS = '#4ade80'
    WARNING = '#fb923c'
    BORDER = '#27272a'
    CHAT_SENT_GRADIENT_1 = '#3b82f6'
    CHAT_SENT_GRADIENT_2 = '#2563eb'
    CHAT_RECEIVED_BG = '#27272a'
    CHAT_RECEIVED_BORDER = '#3f3f46'
    SIDEBAR_BG = '#111113'
    SIDEBAR_HOVER = '#1f1f23'
    SIDEBAR_SELECTED = '#60a5fa'
    INPUT_BG = '#1a1a1e'
    INPUT_BORDER = '#3f3f46'


def get_stylesheet() -> str:
    t = MeshTheme
    return f"""
    QMainWindow, QWidget {{
        background-color: {t.CANVAS};
        color: {t.TEXT};
        font-family: 'Segoe UI', 'Noto Sans', sans-serif;
    }}
    QLabel {{
        color: {t.TEXT};
        background: transparent;
    }}
    QLineEdit {{
        background-color: {t.INPUT_BG};
        color: {t.TEXT};
        border: 1px solid {t.INPUT_BORDER};
        border-radius: 8px;
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
        border-radius: 8px;
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
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t.SURFACE_LIGHT};
        border-radius: 4px;
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
        border-radius: 8px;
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
        border-radius: 8px;
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
    }}
    QGroupBox {{
        border: 1px solid {t.BORDER};
        border-radius: 10px;
        margin-top: 20px;
        padding: 16px 16px 16px 16px;
        font-size: 14px;
        font-weight: 600;
        color: {t.TEXT};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 4px 12px;
        color: {t.TEXT_MUTED};
        font-size: 12px;
        font-weight: 400;
    }}
    QTextEdit {{
        background-color: {t.INPUT_BG};
        color: {t.TEXT};
        border: 1px solid {t.INPUT_BORDER};
        border-radius: 8px;
        padding: 8px;
        font-size: 13px;
    }}
    QTextEdit:focus {{
        border: 2px solid {t.ACCENT};
    }}
    QProgressBar {{
        background-color: {t.SURFACE_VARIANT};
        border: none;
        border-radius: 6px;
        height: 6px;
        text-align: center;
        font-size: 10px;
    }}
    QProgressBar::chunk {{
        background-color: {t.SUCCESS};
        border-radius: 6px;
    }}
    QTableWidget {{
        background-color: transparent;
        border: 1px solid {t.BORDER};
        border-radius: 8px;
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
    """


def get_font(style: str) -> QFont:
    configs = {
        'title': (24, QFont.Weight.Bold),
        'headline': (20, QFont.Weight.Bold),
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
