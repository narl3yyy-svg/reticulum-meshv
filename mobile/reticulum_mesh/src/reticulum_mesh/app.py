"""Reticulum Mesh Mobile App - Enhanced edition."""

import sys
import threading
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.backend import ReticulumNode, LXMFMessenger, ContactManager
    import RNS
    BACKEND_AVAILABLE = True
except Exception as e:
    print(f"Backend import error: {e}")
    BACKEND_AVAILABLE = False
    ReticulumNode = None
    LXMFMessenger = None
    ContactManager = None
    RNS = None


from toga import App, MainWindow, Box, Label, Button, ScrollContainer, TextInput, Switch, Selection
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
    def __init__(self, app_ref):
        super().__init__(style=Pack(direction=COLUMN, flex=1, margin=8))
        self.app_ref = app_ref
        self.rns_node = app_ref.rns_node
        self.lxmf = app_ref.lxmf_messenger
        self.contact_mgr = app_ref.contact_manager
        self.current_dest = ""

        self.add(Label("Messages", style=Pack(font_size=20, margin_bottom=6)))

        dest_row = Box(style=Pack(direction=ROW, margin_bottom=6))
        dest_row.add(Label("To:", style=Pack(margin_right=6)))
        self.dest_input = TextInput(placeholder="64-char hash", style=Pack(flex=1))
        start_btn = Button("Chat", on_press=self.start_chat, style=Pack(width=70))
        dest_row.add(self.dest_input)
        dest_row.add(start_btn)
        self.add(dest_row)

        self.status_label = Label("Enter a destination hash above.", style=Pack(font_size=11, margin_bottom=8))
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

        self.add_bubble("Announce yourself first for discoverability.", is_sent=False)

    def start_chat(self, widget):
        dest = self.dest_input.value.strip().lower().replace(" ", "").replace("-", "")
        if len(dest) == 64:
            self.current_dest = dest
            self.add_bubble(f"Chat started with {dest[:12]}...", is_sent=False)
            self.status_label.text = "Chat active."
        else:
            self.add_bubble("Hash must be 64 characters.", is_sent=False)

    def add_bubble(self, text: str, is_sent: bool = True):
        bubble = ChatBubble(text, is_sent=is_sent, timestamp=get_timestamp())
        self.chat_box.add(bubble)

    def send_message(self, widget):
        if not self.current_dest:
            self.add_bubble("Start a chat first.", is_sent=False)
            return
        text = self.input.value.strip()
        if not text:
            return
        self.add_bubble(text, is_sent=True)
        self.input.value = ""

        sent = False
        if self.lxmf:
            sent = self.lxmf.send_message(self.current_dest, text)
        if not sent and self.rns_node and RNS:
            try:
                dest_bytes = bytes.fromhex(self.current_dest)
                remote_id = RNS.Identity.recall(dest_bytes)
                if remote_id:
                    destination = RNS.Destination(remote_id, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
                else:
                    destination = RNS.Destination(self.rns_node.identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
                    destination.hash = dest_bytes
                RNS.Resource(text.encode("utf-8"), destination)
                sent = True
            except:
                pass

        if not sent:
            self.add_bubble("Send failed", is_sent=False)


class FilesScreen(Box):
    def __init__(self, app_ref):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.add(Label("Files", style=Pack(font_size=20, margin_bottom=8)))
        self.add(Label("File transfers via Reticulum"))
        self.add(Label("Coming in next update: browse, send, receive files."))


class ContactsScreen(Box):
    def __init__(self, app_ref):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.app_ref = app_ref
        self.contact_mgr = app_ref.contact_manager
        self.rns_node = app_ref.rns_node

        self.add(Label("Contacts", style=Pack(font_size=20, margin_bottom=8)))

        announce_btn = Button("Announce Myself", on_press=self.announce)
        self.add(announce_btn)

        self.status = Label("")
        self.add(self.status)

        self.add(Label("\nDiscovered Peers:", style=Pack(font_size=14, margin_top=8)))
        self.peer_label = Label("(refresh to see peers)")
        self.add(self.peer_label)

        refresh_btn = Button("Refresh", on_press=self.refresh)
        self.add(refresh_btn)

        self.add(Label("\nSaved Contacts:", style=Pack(font_size=14, margin_top=8)))
        self.contact_label = Label("(no saved contacts)")
        self.add(self.contact_label)

        self.refresh(None)

    def announce(self, widget):
        announced = False
        if hasattr(self.app_ref, 'lxmf_messenger') and self.app_ref.lxmf_messenger:
            announced = self.app_ref.lxmf_messenger.announce()
        if not announced and self.rns_node:
            announced = self.rns_node.announce_myself()
        self.status.text = "Announced!" if announced else "Announce failed"

    def refresh(self, widget):
        peers = self.rns_node.get_discovered_peers() if self.rns_node else []
        if peers:
            self.peer_label.text = "\n".join([f"{h[:12]}..." for h, _ in peers[:5]])
        else:
            self.peer_label.text = "No peers discovered yet"

        contacts = self.contact_mgr.get_all() if self.contact_mgr else []
        if contacts:
            self.contact_label.text = "\n".join([f"{c.name} ({c.hash_hex[:12]}...)" for c in contacts[:5]])
        else:
            self.contact_label.text = "No saved contacts"


class NetworkScreen(Box):
    def __init__(self, app_ref):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.app_ref = app_ref
        self.rns_node = app_ref.rns_node

        self.add(Label("Network", style=Pack(font_size=20, margin_bottom=8)))

        identity_text = "Not loaded"
        if self.rns_node and hasattr(self.rns_node, "get_identity_hash"):
            try:
                h = self.rns_node.get_identity_hash()
                if h:
                    identity_text = f"Identity:\n{h[:32]}..."
            except:
                pass

        self.add(Label(identity_text, style=Pack(font_size=11, margin_bottom=12)))

        refresh_btn = Button("Refresh Status", on_press=self.refresh)
        self.add(refresh_btn)

        self.status_label = Label("")
        self.add(self.status_label)

        self.refresh(None)

    def refresh(self, widget):
        lines = []
        if self.rns_node:
            peers = self.rns_node.get_discovered_peers()
            lines.append(f"Discovered peers: {len(peers)}")
            if hasattr(self.rns_node, 'reticulum') and self.rns_node.reticulum:
                ifaces = len(getattr(self.rns_node.reticulum, 'interfaces', []))
                lines.append(f"Active interfaces: {ifaces}")
            lines.append(f"Identity hash length: {self.rns_node.hash_length}")
        self.status_label.text = "\n".join(lines) if lines else "No network info"
        self.refresh(None)


class SettingsScreen(Box):
    def __init__(self, app_ref):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.app_ref = app_ref
        self.rns_node = app_ref.rns_node

        self.add(Label("Settings", style=Pack(font_size=20, margin_bottom=10)))

        identity_text = "Your Identity Hash:\n(Not loaded)"
        if self.rns_node and hasattr(self.rns_node, "get_identity_hash"):
            try:
                h = self.rns_node.get_identity_hash()
                if h:
                    identity_text = f"Hash:\n{h}"
            except:
                pass
        self.add(Label(identity_text, style=Pack(margin_bottom=12, font_size=11)))

        announce_btn = Button("Announce Myself", on_press=self.announce)
        self.add(announce_btn)

        self.announce_label = Label("")
        self.add(self.announce_label)

        self.add(Label("\nInterfaces", style=Pack(font_size=16, margin_top=12, margin_bottom=6)))
        self.add(Label("AutoInterface: Enabled"))
        self.add(Label("TCP/Android: Configured in reticulum config"))

        version = Label("\nReticulum Mesh v0.2.0", style=Pack(font_size=10, margin_top=8))
        self.add(version)

    def announce(self, widget):
        announced = False
        if hasattr(self.app_ref, 'lxmf_messenger') and self.app_ref.lxmf_messenger:
            announced = self.app_ref.lxmf_messenger.announce()
        if not announced and self.rns_node:
            announced = self.rns_node.announce_myself()
        self.announce_label.text = "Announced!" if announced else "Failed"


class ReticulumMeshApp(App):
    def startup(self):
        self.main_window = MainWindow(title="Reticulum Mesh")

        self.rns_node = None
        self.lxmf_messenger = None
        self.contact_manager = None

        if BACKEND_AVAILABLE and ReticulumNode:
            try:
                app_config = str(Path.home() / ".config" / "reticulum-mesh-mobile")
                self.rns_node = ReticulumNode(
                    rns_config_dir=str(Path.home() / ".reticulum"),
                    app_config_dir=app_config
                )
                if self.rns_node and self.rns_node.identity:
                    h = self.rns_node.get_identity_hash()
                    print(f"[Mobile] Identity: {h}")

                    if LXMFMessenger:
                        self.lxmf_messenger = LXMFMessenger(
                            self.rns_node.identity,
                            storage_dir=str(Path.home() / ".config" / "reticulum-mesh-mobile" / "lxmf")
                        )
                    if ContactManager:
                        self.contact_manager = ContactManager(app_config)
            except Exception as e:
                print(f"Backend init failed: {e}")

        self.content_box = Box(style=Pack(direction=COLUMN, flex=1))
        self.screen_container = Box(style=Pack(direction=COLUMN, flex=1))

        nav_bar = Box(style=Pack(direction=ROW, margin=4))
        for name, key in [("Chat", "messages"), ("Files", "files"), ("Contacts", "contacts"), ("Network", "network"), ("Settings", "settings")]:
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
            "messages": MessagesScreen(self),
            "files": FilesScreen(self),
            "contacts": ContactsScreen(self),
            "network": NetworkScreen(self),
            "settings": SettingsScreen(self),
        }
        screen = screens.get(screen_name, screens["messages"])
        self.screen_container.add(screen)


def main():
    return ReticulumMeshApp()
