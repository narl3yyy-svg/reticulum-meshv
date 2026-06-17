"""Arch Linux-inspired dark theme for PyQt6."""

from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

class ArchTheme:
    """Dark theme inspired by Arch Linux and Material Design."""
    
    COLORS = {
        'background': '#1E1E1E',
        'surface': '#2A2A2A',
        'surface_variant': '#383838',
        'primary': '#1F88E5',
        'primary_container': '#0D47A1',
        'secondary': '#4CAF50',
        'tertiary': '#FF9800',
        'error': '#F44336',
        'on_background': '#E1E1E1',
        'on_surface': '#E1E1E1',
        'on_primary': '#FFFFFF',
        'outline': '#626262',
    }
    
    COMPONENT_COLORS = {
        'sidebar_bg': '#1A1A1A',
        'sidebar_hover': '#2A2A2A',
        'sidebar_selected': '#1F88E5',
        'chat_bubble_sent': '#1F88E5',
        'chat_bubble_received': '#383838',
        'input_field_bg': '#2A2A2A',
        'input_field_border': '#383838',
        'input_field_focus': '#1F88E5',
        'status_online': '#4CAF50',
        'status_offline': '#757575',
        'file_progress': '#4CAF50',
    }
    
    FONTS = {
        'title': {'size': 24, 'weight': QFont.Weight.Bold},
        'headline': {'size': 20, 'weight': QFont.Weight.Bold},
        'body': {'size': 14, 'weight': QFont.Weight.Normal},
        'small': {'size': 11, 'weight': QFont.Weight.Normal},
    }

def get_stylesheet() -> str:
    """Generate QSS stylesheet."""
    c = ArchTheme.COLORS
    return f"""
    QMainWindow {{ background-color: {c['background']}; color: {c['on_background']}; }}
    QWidget {{ background-color: {c['background']}; color: {c['on_background']}; }}
    QPushButton {{ background-color: {c['primary']}; color: {c['on_primary']}; border: none; padding: 8px 16px; border-radius: 6px; }}
    QPushButton:hover {{ background-color: {c['primary_container']}; }}
    QLineEdit {{ background-color: {c['input_field_bg']}; color: {c['on_surface']}; border: 1px solid {c['input_field_border']}; padding: 8px; border-radius: 6px; }}
    QLineEdit:focus {{ border: 2px solid {c['input_field_focus']}; }}
    QListWidget {{ background-color: {c['sidebar_bg']}; border: none; }}
    QListWidget::item:selected {{ background-color: {c['sidebar_selected']}; color: {c['on_primary']}; }}
    QProgressBar {{ background-color: {c['surface']}; border: none; border-radius: 6px; height: 6px; }}
    QProgressBar::chunk {{ background-color: {c['file_progress']}; border-radius: 6px; }}
    """

def get_font(style: str) -> QFont:
    """Get themed font."""
    config = ArchTheme.FONTS.get(style, ArchTheme.FONTS['body'])
    font = QFont()
    font.setPointSize(config['size'])
    font.setWeight(config['weight'])
    return font
