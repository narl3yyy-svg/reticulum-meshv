"""Reticulum Mesh Mobile - Better identity visibility + interface settings."""

import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.backend import ReticulumNode
    import RNS
    BACKEND_AVAILABLE = True
except Exception:
    BACKEND_AVAILABLE = False
    ReticulumNode = None
    RNS = None


from toga import App, MainWindow, Box, Label, Button, ScrollContainer, TextInput, Switch
try:
    from toga.style import Pack
    from toga.constants import COLUMN, ROW
except ImportError:
    from toga.style.pack import Pack
    from toga.constants import COLUMN, ROW


def get_timestamp():
    from datetime import datetime
    return datetime.now().strftime("%H:%M")


class ChatBubble(Box):
    def __init__(self, text: str, is_sent: bool = True, timestamp: str = ""):
        super().__init__(
            style=Pack(
                direction=COLUMN,
                margin=5,
                margin_left=65 if is_sent else 8,
                margin_right=8 if is_sent else 65,
            )
        )
        self.add(Label(text, style=Pack(margin=8, margin_bottom=2)))
        if timestamp:
            self.add(Label(timestamp, style=Pack(margin=8, margin_top=0, font_size=10)))


class MessagesScreen(Box):
    def __init__(self, rns_node=None):
        super().__init__(style=Pack(direction=COLUMN, flex=1, margin=8))

        self.rns_node = rns_node
        self.current_dest = ""

        self.add(Label("Messages", style=Pack(font_size=20, margin_bottom=6)))

        dest_row = Box(style=Pack(direction=ROW, margin_bottom=6))
        dest_row.add(Label("To:", style=Pack(margin_right=6)))
        self.dest_input = TextInput(placeholder="64-char destination hash", style=Pack(flex=1))
        start_btn = Button("Start Chat", on_press=self.start_chat, style=Pack(width=90))
        dest_row.add(self.dest_input)
        dest_row.add(start_btn)
        self.add(dest_row)

        self.status_label = Label("Enter the other device's full 64-char hash above, then tap Start.", style=Pack(font_size=11, margin_bottom=8))
        self.add(self.status_label)

        self.scroll = ScrollContainer(style=Pack(flex=1))
        self.chat_box = Box(style=Pack(direction=COLUMN))
        self.scroll.content = self.chat_box
        self.add(self.scroll)

        input_row = Box(style=Pack(direction=ROW, margin_top=8))
        self.input = TextInput(placeholder="Type a message...", style=Pack(flex=1, margin_right=8))
        send_btn = Button("Send", on_press=self.send_message, style=Pack(width=70))
        input_row.add(self.input)
        input_row.add(send_btn)
        self.add(input_row)

        self.add_bubble("Tip: Both sides should tap Announce first.", is_sent=False)

    def start_chat(self, widget):
        dest = self.dest_input.value.strip().lower().replace(" ", "").replace("-", "")
        if len(dest) == 64:
            self.current_dest = dest
            self.add_bubble(f"Chat started with {dest[:12]}...", is_sent=False)
            self.status_label.text = "Chat active. Type below and tap Send."
        else:
            self.add_bubble("Hash must be exactly 64 characters (no extra text).", is_sent=False)

    def add_bubble(self, text: str, is_sent: bool = True):
        bubble = ChatBubble(text, is_sent=is_sent, timestamp=get_timestamp())
        self.chat_box.add(bubble)

    def send_message(self, widget):
        if not self.current_dest:
            self.add_bubble("Please start a chat first (enter hash above).", is_sent=False)
            return

        text = self.input.value.strip()
        if not text:
            return

        self.add_bubble(text, is_sent=True)
        self.input.value = ""

        if BACKEND_AVAILABLE and self.rns_node and RNS:
            try:
                dest_bytes = bytes.fromhex(self.current_dest)
                remote_id = RNS.Identity.recall(dest_bytes)

                if remote_id:
                    destination = RNS.Destination(remote_id, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
                else:
                    destination = RNS.Destination(self.rns_node.identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
                    destination.hash = dest_bytes

                RNS.Resource(text.encode("utf-8"), destination)
                print(f"[Mobile] Message sent via Reticulum")
            except Exception as e:
                print(f"[Mobile] Send error: {e}")
                self.add_bubble("Failed to send via Reticulum (check logs).", is_sent=False)
        else:
            print(f"[Mobile] Backend not ready. Message only shown locally: {text}")


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
    def __init__(self, rns_node=None):
        super().__init__(style=Pack(direction=COLUMN, margin=10))

        self.rns_node = rns_node

        self.add(Label("Settings", style=Pack(font_size=20, margin_bottom=10)))

        # === Identity ===
        identity_text = "Your Identity Hash:\n(Not available yet - backend not ready)"
        if rns_node and hasattr(rns_node, "get_identity_hash"):
            try:
                my_hash = rns_node.get_identity_hash()
                if my_hash:
                    identity_text = f"Your Identity Hash:\n{my_hash}"
            except:
                pass

        self.add(Label(identity_text, style=Pack(margin_bottom=12, font_size=11)))

        # Announce button
        announce_btn = Button("Announce Myself", on_press=self.announce_myself)
        self.add(announce_btn)

        self.announce_status = Label("")
        self.add(self.announce_status)

        # === Interfaces (basic) ===
        self.add(Label("\nInterfaces", style=Pack(font_size=16, margin_top=12, margin_bottom=6)))

        self.auto_switch = Switch("AutoInterface", value=True)
        self.add(self.auto_switch)

        self.tcp_switch = Switch("TCP Client to desktop", value=True)
        self.add(self.tcp_switch)

        note = Label("Interface changes require app restart. Full config editing coming soon.", style=Pack(font_size=10, margin_top=6))
        self.add(note)

    def announce_myself(self, widget):
        if self.rns_node and hasattr(self.rns_node, "announce_myself"):
            success = self.rns_node.announce_myself()
            if success:
                self.announce_status.text = "Announced successfully!"
                print("[Mobile] Announced successfully")
            else:
                self.announce_status.text = "Announce failed (backend issue)."
                print("[Mobile] Announce failed")
        else:
            self.announce_status.text = "Cannot announce - backend not ready"
            print("[Mobile] Cannot announce - backend not ready")


class ReticulumMeshApp(App):
    def startup(self):
        self.main_window = MainWindow(title="Reticulum Mesh")

        self.rns_node = None
        if BACKEND_AVAILABLE and ReticulumNode:
            try:
                self.rns_node = ReticulumNode(
                    rns_config_dir=str(Path.home() / ".reticulum"),
                    app_config_dir=str(Path.home() / ".config" / "reticulum-mesh-mobile")
                )
                if self.rns_node:
                    try:
                        my_hash = self.rns_node.get_identity_hash()
                        print(f"[Mobile] This device's identity hash: {my_hash}")
                    except:
                        pass
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
        if screen_name == "messages":
            self.screen_container.add(MessagesScreen(self.rns_node))
        elif screen_name == "files":
            self.screen_container.add(FilesScreen())
        elif screen_name == "contacts":
            self.screen_container.add(ContactsScreen())
        elif screen_name == "settings":
            self.screen_container.add(SettingsScreen(self.rns_node))


def main():
    return ReticulumMeshApp()
