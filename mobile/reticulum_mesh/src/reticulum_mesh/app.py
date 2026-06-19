"""Reticulum Mesh Mobile App - Improved version with chat-like Messages screen."""

import sys
from pathlib import Path

# Try to import backend (works on desktop dev, may fail on Android for now)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.backend import ReticulumNode
    BACKEND_AVAILABLE = True
except Exception:
    BACKEND_AVAILABLE = False
    ReticulumNode = None


from toga import App, MainWindow, Box, Label, Button, ScrollContainer, TextInput
try:
    from toga.style import Pack
    from toga.constants import COLUMN, ROW
except ImportError:
    # Fallback for very old Toga versions
    from toga.style.pack import Pack
    from toga.constants import COLUMN, ROW


class ChatBubble(Box):
    """Simple chat bubble using Toga components."""
    def __init__(self, text: str, is_sent: bool = True, timestamp: str = ""):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                margin=4,
                margin_left=60 if is_sent else 8,
                margin_right=8 if is_sent else 60,
            )
        )

        # Message text
        msg_label = Label(
            text,
            style=Pack(
                margin=8,
                margin_bottom=2,
            )
        )
        self.add(msg_label)

        if timestamp:
            time_label = Label(
                timestamp,
                style=Pack(
                    margin=8,
                    margin_top=0,
                    font_size=10,
                )
            )
            self.add(time_label)


class MessagesScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, flex=1, margin=8))

        # Header
        header = Label("Messages", style=Pack(font_size=20, margin_bottom=8))
        self.add(header)

        # Message list
        self.message_list = ScrollContainer(style=Pack(flex=1))
        self.message_container = Box(style=Pack(direction=COLUMN))
        self.message_list.content = self.message_container
        self.add(self.message_list)

        # Input area
        input_row = Box(style=Pack(direction=ROW, margin_top=8))
        self.input = TextInput(placeholder="Type a message...", style=Pack(flex=1, margin_right=8))
        send_btn = Button("Send", on_press=self.send_message, style=Pack(width=80))
        input_row.add(self.input)
        input_row.add(send_btn)
        self.add(input_row)

        # Welcome message
        self.add_bubble("Welcome to Reticulum Mesh!", is_sent=False)

    def add_bubble(self, text: str, is_sent: bool = True):
        timestamp = "now"
        bubble = ChatBubble(text, is_sent=is_sent, timestamp=timestamp)
        self.message_container.add(bubble)

    def send_message(self, widget):
        text = self.input.value.strip()
        if not text:
            return

        self.add_bubble(text, is_sent=True)
        self.input.value = ""

        # TODO: Send via ReticulumNode when properly integrated
        print(f"[Mobile] Would send message: {text}")


class FilesScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.add(Label("Files", style=Pack(font_size=20, margin_bottom=10)))
        self.add(Label("File transfer over Reticulum will be available here."))


class ContactsScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.add(Label("Contacts", style=Pack(font_size=20, margin_bottom=10)))
        self.add(Label("Discovered peers from the Reticulum network will appear here."))


class SettingsScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.add(Label("Settings", style=Pack(font_size=20, margin_bottom=10)))
        status = "Backend connected" if BACKEND_AVAILABLE else "Backend not available yet (desktop only for now)"
        self.add(Label(status))


class ReticulumMeshApp(App):
    def startup(self):
        self.main_window = MainWindow(title="Reticulum Mesh")

        # Try to initialize backend (non-fatal on Android for now)
        self.rns_node = None
        if BACKEND_AVAILABLE and ReticulumNode:
            try:
                self.rns_node = ReticulumNode(
                    rns_config_dir=str(Path.home() / ".reticulum"),
                    app_config_dir=str(Path.home() / ".config" / "reticulum-mesh-mobile")
                )
                print("ReticulumNode initialized on mobile.")
            except Exception as e:
                print(f"Could not initialize ReticulumNode: {e}")

        # Main layout
        self.content_box = Box(style=Pack(direction=COLUMN, flex=1))
        self.screen_container = Box(style=Pack(direction=COLUMN, flex=1))

        # Bottom navigation
        nav_bar = Box(style=Pack(direction=ROW, margin=4))
        for name, key in [("Messages", "messages"), ("Files", "files"), ("Contacts", "contacts"), ("Settings", "settings")]:
            btn = Button(name, on_press=lambda w, k=key: self.show_screen(k))
            btn.style.flex = 1
            nav_bar.add(btn)

        self.content_box.add(self.screen_container)
        self.content_box.add(nav_bar)

        self.main_window.content = self.content_box
        self.main_window.show()

        self.show_screen("messages")

    def show_screen(self, screen):
        self.screen_container.clear()
        screens = {
            "messages": MessagesScreen,
            "files": FilesScreen,
            "contacts": ContactsScreen,
            "settings": SettingsScreen,
        }
        if screen in screens:
            self.screen_container.add(screens[screen]())


def main():
    return ReticulumMeshApp()
