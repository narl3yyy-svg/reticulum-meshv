"""MeshChatX-matched dark theme for PyQt6."""

from PyQt6.QtGui import QFont


class MeshTheme:
    CANVAS = '#09090b'
    SURFACE = '#18181b'
    SURFACE_VARIANT = '#27272a'
    SURFACE_LIGHT = '#3f3f46'
    TEXT = '#f3f4f6'
    TEXT_SECONDARY = '#ffffff'
    TEXT_MUTED = '#9ca3af'
    TEXT_DIM = '#71717a'
    ACCENT = '#60a5fa'
    ACCENT_DARK = '#3b82f6'
    ACCENT_LIGHT = '#93c5fd'
    ACTION_PRIMARY = '#2563eb'
    ACTION_PRIMARY_HOVER = '#3b82f6'
    ERROR = '#f87171'
    SUCCESS = '#34d399'
    WARNING = '#fb923c'
    INFO = '#38bdf8'
    BORDER = '#3f3f46'
    BORDER_CARD = '#27272a'
    BORDER_STRONG = '#52525b'
    CHAT_SENT_BG = '#2563eb'
    CHAT_SENT_GRADIENT_1 = '#2563eb'
    CHAT_SENT_GRADIENT_2 = '#1d4ed8'
    CHAT_RECEIVED_BG = '#18181b'
    CHAT_RECEIVED_BORDER = '#27272a'
    SIDEBAR_BG = '#09090b'
    SIDEBAR_HOVER = '#27272a'
    SIDEBAR_SELECTED = '#2563eb'
    INPUT_BG = '#18181b'
    INPUT_BORDER = '#3f3f46'
    BADGE_BG = '#2563eb'
    BADGE_TEXT = '#ffffff'
    LINK = '#60a5fa'
    HEADING = '#f3f4f6'
    MUTED_HEADING = '#9ca3af'
    FOCUS = '#3b82f6'
    SCROLLBAR_THUMB = '#52525b'
    SCROLLBAR_TRACK = '#27272a'


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
        border-radius: 12px;
        padding: 10px 14px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 2px solid {t.FOCUS};
        padding: 9px 13px;
    }}
    QLineEdit::placeholder {{
        color: {t.TEXT_DIM};
    }}
    QPushButton {{
        background-color: {t.ACTION_PRIMARY};
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {t.ACTION_PRIMARY_HOVER};
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
        background: {t.SCROLLBAR_THUMB};
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
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {t.SCROLLBAR_THUMB};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
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
        background-color: {t.SIDEBAR_HOVER};
        color: {t.ACCENT};
    }}
    QTreeWidget {{
        background-color: transparent;
        border: 1px solid {t.BORDER_CARD};
        border-radius: 12px;
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
        border: 1px solid {t.BORDER_CARD};
        border-radius: 16px;
        margin-top: 20px;
        padding: 16px;
        font-size: 13px;
        font-weight: 600;
        color: {t.TEXT};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 12px;
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
        border-radius: 12px;
        padding: 10px;
        font-size: 13px;
    }}
    QTextEdit:focus {{
        border: 2px solid {t.FOCUS};
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
        border: 1px solid {t.BORDER_CARD};
        border-radius: 12px;
        gridline-color: {t.BORDER_CARD};
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        color: {t.TEXT};
    }}
    QTableWidget::item:selected {{
        background-color: {t.ACTION_PRIMARY};
        color: white;
    }}
    QSplitter::handle {{
        background-color: {t.BORDER_CARD};
        width: 1px;
    }}
    QStatusBar {{
        background-color: {t.SURFACE};
        border-top: 1px solid {t.BORDER_CARD};
        color: {t.TEXT_MUTED};
        font-size: 12px;
    }}
    QMenu {{
        background-color: {t.SURFACE};
        border: 1px solid {t.BORDER};
        border-radius: 12px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 8px;
        font-size: 13px;
    }}
    QMenu::item:selected {{
        background-color: {t.ACTION_PRIMARY};
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
        border-radius: 12px;
        padding: 10px 14px;
        font-size: 13px;
    }}
    QComboBox:focus {{
        border: 2px solid {t.FOCUS};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox::item:selected {{
        background-color: {t.ACTION_PRIMARY};
        color: white;
    }}
    QCheckBox {{
        color: {t.TEXT};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {t.BORDER_STRONG};
        background: {t.INPUT_BG};
    }}
    QCheckBox::indicator:checked {{
        background: {t.ACTION_PRIMARY};
        border: 1px solid {t.ACTION_PRIMARY};
    }}
    QTabWidget::pane {{
        border: 1px solid {t.BORDER_CARD};
        border-radius: 12px;
        background: {t.SURFACE};
    }}
    QTabBar::tab {{
        background: transparent;
        color: {t.TEXT_MUTED};
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        color: {t.ACCENT};
        border-bottom: 2px solid {t.ACCENT};
    }}
    QTabBar::tab:hover {{
        color: {t.TEXT};
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
