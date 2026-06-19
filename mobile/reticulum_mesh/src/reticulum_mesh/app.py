"""Reticulum Mesh Mobile - Improved Messages tab with chat bubbles and Reticulum sending."""

import sys
from pathlib import Path

# Try to import backend (graceful fallback on Android)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.backend import ReticulumNode
    import RNS
    BACKEND_AVAILABLE = True
except Exception:
    BACKEND_AVAILABLE = False
    ReticulumNode = None
    RNS = None


from toga import App, MainWindow, Box, Label, Button, ScrollContainer, TextInput
try:
    from toga.style import Pack
    from toga.constants import COLUMN, ROW
except ImportError:
    from toga.style.pack import Pack
    from toga.constants import COLUMN, ROW


def format_time():
    from datetime import datetime
    return datetime.now().strftime("%H:%M")


class ChatBubble(Box):
    """Nice chat bubble component."""
    def __init__(self, text: str, is_sent: bool = True, timestamp: str = ""):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                margin=6,
                margin_left=70 if is_sent else 10,
                margin_right=10 if is_sent else 70,
            )
        )

        # Message text
        msg = Label(text, style=Pack(margin=10, margin_bottom=2))
        self.add(msg)

        if timestamp:
            time_label = Label(timestamp, style=Pack(margin=10, margin_top=0, font_size=10))
            self.add(time_label)


class MessagesScreen(Box):
    def __init__(self, rns_node=None):
        super().__init__(style=Pack(direction=COLUMN, flex=1, margin=8))

        self.rns_node = rns_node
        self.current_dest = ""

        # Header
        header = Label("Messages", style=Pack(font_size=20, margin_bottom=6))
        self.add(header)

        # Destination input
        dest_row = Box(style=Pack(direction=ROW, margin_bottom=8))
        dest_row.add(Label("To:", style=Pack(margin_right=6)))
        self.dest_input = TextInput(placeholder="64-char destination hash", style=Pack(flex=1))
        start_btn = Button("Start Chat", on_press=self.start_chat, style=Pack(width=100))
        dest_row.add(self.dest_input)
        dest_row.add(start_btn)
        self.add(dest_row)

        # Chat area
        self.scroll = ScrollContainer(style=Pack(flex=1))
        self.messages_box = Box(style=Pack(direction=COLUMN))
        self.scroll.content = self.messages_box
        self.add(self.scroll)

        # Input bar
        input_row = Box(style=Pack(direction=ROW, margin_top=8))
        self.input = TextInput(placeholder="Type a message...", style=Pack(flex=1, margin_right=8))
        send_btn = Button("Send", on_press=self.send_message, style=Pack(width=80))
        input_row.add(self.input)
        input_row.add(send_btn)
        self.add(input_row)

        # Welcome
        self.add_bubble("Welcome! Enter a destination hash above to start chatting.", is_sent=False)

    def start_chat(self, widget):
        dest = self.dest_input.value.strip().lower()
        if len(dest) == 64:
            self.current_dest = dest
            self.add_bubble(f"Now chatting with {dest[:12]}...", is_sent=False)
        else:
            self.add_bubble("Please enter a valid 64-character hash.", is_sent=False)

    def add_bubble(self, text: str, is_sent: bool = True):
        bubble = ChatBubble(text, is_sent=is_sent, timestamp=format_time())
        self.messages_box.add(bubble)

    def send_message(self, widget):
        if not self.current_dest:
            self.add_bubble("Please enter a destination hash first.", is_sent=False)
            return

        text = self.input.value.strip()
        if not text:
            return

        self.add_bubble(text, is_sent=True)
        self.input.value = ""

        # Try to send via Reticulum if available
        if BACKEND_AVAILABLE and self.rns_node and RNS:
            try:
                dest_bytes = bytes.fromhex(self.current_dest)
                remote_identity = RNS.Identity.recall(dest_bytes)

                if remote_identity:
                    destination = RNS.Destination(
                        remote_identity,
                        RNS.Destination.OUT,
                        RNS.Destination.SINGLE,
                        "reticulum-meshv",
                        "filetransfer"
                    )
                else:
                    # Fallback
                    destination = RNS.Destination(
                        self.rns_node.identity,
                        RNS.Destination.OUT,
                        RNS.Destination.SINGLE,
                        "reticulum-meshv",
                        "filetransfer"
                    )
                    destination.hash = dest_bytes

                RNS.Resource(text.encode("utf-8"), destination)
                print(f"[Mobile] Message sent via Reticulum: {text}")
            except Exception as e:
                print(f"[Mobile] Failed to send via Reticulum: {e}")
                self.add_bubble("Failed to send (backend error).", is_sent=False)
        else:
            print(f"[Mobile] Backend not available. Message: {text}")


class FilesScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.add(Label("Files", style=Pack(font_size=20, margin_bottom=8)))
        self.add(Label("File transfer coming soon."))


class ContactsScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.add(Label("Contacts", style=Pack(font_size=20, margin_bottom=8)))
        self.add(Label("Discovered peers will appear here."))


class SettingsScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.add(Label("Settings", style=Pack(font_size=20, margin_bottom=8)))
        status = "Reticulum backend: Connected" if BACKEND_AVAILABLE else "Reticulum backend: Not available on this build"
        self.add(Label(status))


class ReticulumMeshApp(App):
    def startup(self):
        self.main_window = MainWindow(title="Reticulum Mesh")

        # Try to initialize ReticulumNode
        self.rns_node = None
        if BACKEND_AVAILABLE and ReticulumNode:
            try:
                self.rns_node = ReticulumNode(
                    rns_config_dir=str(Path.home() / ".reticulum"),
                    app_config_dir=str(Path.home() / ".config" / "reticulum-mesh-mobile")
                )
            except Exception as e:
                print(f"ReticulumNode init failed: {e}")

        self.content_box = Box(style=Pack(direction=COLUMN, flex=1))
        self.screen_container = Box(style=Pack(direction=COLUMN, flex=1))

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

    def show_screen(self, screen_name):
        self.screen_container.clear()
        screens = {
            "messages": lambda: MessagesScreen(self.rns_node),
            "files": FilesScreen,
            "contacts": ContactsScreen,
            "settings": SettingsScreen,
        }
        if screen_name in screens:
            self.screen_container.add(screens[screen_name]())


def main():
    return ReticulumMeshApp()
