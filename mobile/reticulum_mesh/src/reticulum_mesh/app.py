"""Reticulum Mesh Mobile App - Self-contained."""

import sys
import time
import threading
from pathlib import Path

BACKEND_AVAILABLE = False
try:
    import RNS
    BACKEND_AVAILABLE = True
except ImportError:
    RNS = None

try:
    import LXMF
except ImportError:
    LXMF = None

from toga import App, MainWindow, Box, Label, Button, ScrollContainer, TextInput
try:
    from toga.style import Pack
    from toga.constants import COLUMN, ROW
except ImportError:
    from toga.style.pack import Pack
    from toga.constants import COLUMN, ROW


def get_timestamp():
    from datetime import datetime
    return datetime.now().strftime("%H:%M")


class MobileReticulumNode:
    def __init__(self):
        self.reticulum = None
        self.identity = None
        self.identity_hash = ""
        self.discovered_peers = {}

        if not BACKEND_AVAILABLE:
            return

        try:
            config_dir = str(Path.home() / ".reticulum")
            self.reticulum = RNS.Reticulum(configdir=config_dir)
            self.identity = self._load_identity()
            self.identity_hash = self.identity.hash.hex() if self.identity else ""

            try:
                RNS.Transport.register_announce_handler(self._on_announce)
            except:
                pass
        except Exception as e:
            print(f"[Mobile] RNS init error: {e}")

    def _load_identity(self):
        path = Path.home() / ".config" / "reticulum-mesh-mobile" / "identity.key"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            try:
                identity = RNS.Identity.from_file(str(path))
                if identity and identity.hash:
                    return identity
            except:
                pass
            try:
                path.unlink(missing_ok=True)
            except:
                pass
        identity = RNS.Identity()
        identity.to_file(str(path))
        return identity

    def _on_announce(self, destination_hash, announced_identity, app_data):
        if not announced_identity:
            return
        hash_hex = destination_hash.hex() if hasattr(destination_hash, 'hex') else destination_hash
        self.discovered_peers[hash_hex] = {
            "name": announced_identity.hash.hex()[:12] if announced_identity else hash_hex[:12],
            "last_seen": time.time(),
        }

    def get_identity_hash(self):
        return self.identity_hash

    def get_discovered_peers(self):
        return list(self.discovered_peers.items())

    def announce_myself(self):
        try:
            dest = RNS.Destination(
                self.identity,
                RNS.Destination.IN,
                RNS.Destination.SINGLE,
                "reticulum-meshv",
                "announce"
            )
            dest.announce()
            return True
        except:
            return False

    def send_text(self, destination_hash, text):
        if not BACKEND_AVAILABLE:
            return False
        try:
            dest_bytes = bytes.fromhex(destination_hash)
            remote_id = RNS.Identity.recall(dest_bytes)
            if not remote_id:
                remote_id = RNS.Identity()
                remote_id.hash = dest_bytes

            if LXMF:
                router = LXMF.LXMRouter(identity=self.identity)
                dest = RNS.Destination(remote_id, RNS.Destination.OUT, RNS.Destination.SINGLE, "lxmf", "delivery")
                msg = LXMF.LXMessage(dest, self.identity, content=text.encode("utf-8"))
                router.handle_outbound(msg)
                return True
            else:
                dest = RNS.Destination(remote_id, RNS.Destination.OUT, RNS.Destination.SINGLE, "reticulum-meshv", "filetransfer")
                RNS.Resource(text.encode("utf-8"), dest)
                return True
        except:
            return False


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
    def __init__(self, node):
        super().__init__(style=Pack(direction=COLUMN, flex=1, margin=8))
        self.node = node
        self.current_dest = ""

        self.add(Label("Messages", style=Pack(font_size=20, margin_bottom=6)))

        dest_row = Box(style=Pack(direction=ROW, margin_bottom=6))
        dest_row.add(Label("To:", style=Pack(margin_right=6)))
        self.dest_input = TextInput(placeholder="64-char hash", style=Pack(flex=1))
        start_btn = Button("Chat", on_press=self.start_chat, style=Pack(width=70))
        dest_row.add(self.dest_input)
        dest_row.add(start_btn)
        self.add(dest_row)

        self.status_label = Label("Enter a destination hash.", style=Pack(font_size=11, margin_bottom=8))
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

        sent = self.node.send_text(self.current_dest, text) if self.node else False
        if not sent:
            self.add_bubble("Send failed (Reticulum not ready)", is_sent=False)


class ContactsScreen(Box):
    def __init__(self, node):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.node = node

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

        self.refresh(None)

    def announce(self, widget):
        if self.node:
            ok = self.node.announce_myself()
            self.status.text = "Announced!" if ok else "Failed"

    def refresh(self, widget):
        if not self.node:
            self.peer_label.text = "Reticulum not available"
            return
        peers = self.node.get_discovered_peers()
        if peers:
            self.peer_label.text = "\n".join([f"{h[:12]}..." for h, _ in peers[:5]])
        else:
            self.peer_label.text = "No peers discovered"


class NetworkScreen(Box):
    def __init__(self, node):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.node = node

        self.add(Label("Network", style=Pack(font_size=20, margin_bottom=8)))

        hash_text = "Not loaded"
        if self.node:
            h = self.node.get_identity_hash()
            if h:
                hash_text = f"Identity:\n{h[:32]}..."
        self.add(Label(hash_text, style=Pack(font_size=11, margin_bottom=12)))

        refresh_btn = Button("Refresh", on_press=self.refresh)
        self.add(refresh_btn)

        self.status = Label("")
        self.add(self.status)

        self.refresh(None)

    def refresh(self, widget):
        if not self.node:
            self.status.text = "Reticulum not available"
            return
        peers = self.node.get_discovered_peers()
        self.status.text = f"Peers discovered: {len(peers)}"


class SettingsScreen(Box):
    def __init__(self, node):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.node = node
        self.add(Label("Settings", style=Pack(font_size=20, margin_bottom=10)))

        hash_text = "Not loaded"
        if self.node:
            h = self.node.get_identity_hash()
            if h:
                hash_text = f"Hash:\n{h}"
        self.add(Label(hash_text, style=Pack(margin_bottom=12, font_size=11)))

        announce_btn = Button("Announce Myself", on_press=self.announce)
        self.add(announce_btn)
        self.announce_label = Label("")
        self.add(self.announce_label)

        self.add(Label("\nInterfaces", style=Pack(font_size=16, margin_top=12, margin_bottom=6)))
        self.add(Label("AutoInterface: Enabled"))
        version = Label("\nReticulum Mesh v0.2.0", style=Pack(font_size=10, margin_top=8))
        self.add(version)

    def announce(self, widget):
        if self.node:
            ok = self.node.announce_myself()
            self.announce_label.text = "Announced!" if ok else "Failed"


class ReticulumMeshApp(App):
    def startup(self):
        self.main_window = MainWindow(title="Reticulum Mesh")
        self.node = MobileReticulumNode()

        self.content_box = Box(style=Pack(direction=COLUMN, flex=1))
        self.screen_container = Box(style=Pack(direction=COLUMN, flex=1))

        nav_bar = Box(style=Pack(direction=ROW, margin=4))
        for name, key in [("Chat", "chat"), ("Contacts", "contacts"), ("Network", "network"), ("Settings", "settings")]:
            btn = Button(name, on_press=lambda w, k=key: self.show_screen(k))
            btn.style.flex = 1
            nav_bar.add(btn)

        self.content_box.add(self.screen_container)
        self.content_box.add(nav_bar)
        self.main_window.content = self.content_box
        self.main_window.show()
        self.show_screen("chat")

    def show_screen(self, screen_name):
        self.screen_container.clear()
        screens = {
            "chat": MessagesScreen(self.node),
            "contacts": ContactsScreen(self.node),
            "network": NetworkScreen(self.node),
            "settings": SettingsScreen(self.node),
        }
        self.screen_container.add(screens.get(screen_name, screens["chat"]))


def main():
    return ReticulumMeshApp()
