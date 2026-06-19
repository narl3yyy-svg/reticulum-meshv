"""RMESHV Mobile - TCP bridge client for desktop relay."""
import os
import sys
import time
import json
import socket
import threading
from pathlib import Path

from toga import App, MainWindow, Box, Label, Button, ScrollContainer, TextInput, Selection
try:
    from toga.style import Pack
    from toga.constants import COLUMN, ROW
except ImportError:
    from toga.style.pack import Pack
    from toga.constants import COLUMN, ROW


def log(*args):
    msg = " ".join(str(a) for a in args)
    try:
        from android import log as android_log
        android_log.v("RMESHV", msg)
    except ImportError:
        print(f"[RM] {msg}")


def get_timestamp():
    from datetime import datetime
    return datetime.now().strftime("%H:%M")


LOCAL_STORE = Path.home() / ".config" / "rmeshv"


class BridgeClient:
    def __init__(self):
        self.sock = None
        self.rx_thread = None
        self.connected = False
        self.server_identity = ""
        self.local_identity = self._load_identity()
        self.recv_queue = []
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self.pending_ping = None

    def _load_identity(self):
        LOCAL_STORE.mkdir(parents=True, exist_ok=True)
        p = LOCAL_STORE / "identity.txt"
        if p.exists():
            try:
                v = p.read_text().strip()
                if len(v) == 64:
                    return v
            except:
                pass
        v = os.urandom(32).hex()
        try:
            p.write_text(v)
        except:
            pass
        return v

    def connect(self, host, port):
        self.disconnect()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((host, port))
            self.sock.settimeout(None)
            self.connected = True
            self._stop.clear()
            self.rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
            self.rx_thread.start()
            self._send({"type": "hello", "identity": self.local_identity})
            return True
        except Exception as e:
            log(f"Bridge connect failed: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self._stop.set()
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        self.connected = False
        self.server_identity = ""

    def _send(self, data):
        if not self.sock:
            return
        try:
            blob = json.dumps(data) + "\n"
            self.sock.sendall(blob.encode("utf-8"))
        except:
            self.disconnect()

    def _rx_loop(self):
        buf = b""
        while not self._stop.is_set():
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line.decode("utf-8"))
                        self._handle_msg(msg)
                    except:
                        pass
            except:
                if not self._stop.is_set():
                    time.sleep(0.1)
        self.connected = False
        self.server_identity = ""

    def _handle_msg(self, msg):
        t = msg.get("type", "")
        if t == "welcome":
            self.server_identity = msg.get("server_identity", "")
        with self.lock:
            self.recv_queue.append(msg)

    def poll_messages(self):
        with self.lock:
            items = self.recv_queue.copy()
            self.recv_queue.clear()
        return items

    def send_text(self, dest, text):
        self._send({"type": "message", "to": dest, "text": text, "timestamp": time.time()})

    def announce(self):
        self._send({"type": "announce"})

    def send_peers_request(self):
        self._send({"type": "get_peers"})


def make_label(text, size=11, margin_b=6):
    l = Label(text)
    l.style.font_size = size
    l.style.margin_bottom = margin_b
    return l


class MessagesScreen(Box):
    def __init__(self, app_ref, node):
        super().__init__()
        self.style.direction = COLUMN
        self.style.flex = 1
        self.style.margin = 8
        self.app_ref = app_ref
        self.node = node
        self.current_dest = node.server_identity if node else ""

        self.add(make_label("Messages", size=20, margin_b=6))

        dest_row = Box()
        dest_row.style.direction = ROW
        dest_row.style.margin_bottom = 6
        to_lbl = Label("To:")
        to_lbl.style.margin_right = 6
        dest_row.add(to_lbl)
        self.dest_input = TextInput(placeholder="64-char hash (blank = desktop)")
        self.dest_input.style.flex = 1
        start_btn = Button("Chat", on_press=self.start_chat)
        start_btn.style.width = 70
        dest_row.add(self.dest_input)
        dest_row.add(start_btn)
        self.add(dest_row)

        self.status_label = make_label("Enter destination hash or leave blank for desktop.")
        self.add(self.status_label)

        self.scroll = ScrollContainer()
        self.scroll.style.flex = 1
        self.chat_box = Box()
        self.chat_box.style.direction = COLUMN
        self.scroll.content = self.chat_box
        self.add(self.scroll)

        input_row = Box()
        input_row.style.direction = ROW
        input_row.style.margin_top = 8
        self.input = TextInput(placeholder="Type a message...")
        self.input.style.flex = 1
        self.input.style.margin_right = 8
        send_btn = Button("Send", on_press=self.send_message)
        send_btn.style.width = 70
        input_row.add(self.input)
        input_row.add(send_btn)
        self.add(input_row)

        self._poll_timer = None
        self._start_poll()

    def _start_poll(self):
        self._poll()

    def _poll(self):
        try:
            if self.node and self.node.connected:
                msgs = self.node.poll_messages()
                for msg in msgs:
                    self._handle_incoming(msg)
        except:
            pass
        if self.app_ref and self.app_ref._running:
            from toga import App
            try:
                App.app.add_background_task(lambda a: None)
            except:
                pass
        self._poll_timer = threading.Timer(0.5, self._poll)
        self._poll_timer.daemon = True
        self._poll_timer.start()

    def _handle_incoming(self, msg):
        t = msg.get("type", "")
        if t == "message":
            sender = msg.get("from", "unknown")[:16]
            text = msg.get("text", "")
            ts = msg.get("timestamp", time.time())
            self.add_bubble(f"[{sender}] {text}", is_sent=False)
        elif t == "peers":
            peers = msg.get("peers", [])
            self.add_bubble(f"Peers on bridge: {len(peers)}", is_sent=False)
        elif t == "welcome":
            sid = msg.get("server_identity", "")[:16]
            self.add_bubble(f"Connected to bridge [{sid}]", is_sent=False)

    def start_chat(self, widget):
        dest = "".join(c for c in self.dest_input.value.strip() if c in "0123456789abcdefABCDEF").lower()
        if len(dest) == 64 or not dest:
            self.current_dest = dest
            label = "desktop" if not dest else f"{dest[:12]}..."
            self.add_bubble(f"Chat started with {label}", is_sent=False)
            self.status_label.text = f"Target: {label}"
        else:
            self.add_bubble(f"Hash must be 64 hex chars, got {len(dest)}.", is_sent=False)

    def add_bubble(self, text, is_sent=True):
        box = Box()
        box.style.margin = 5
        box.style.margin_left = 65 if is_sent else 8
        box.style.margin_right = 8 if is_sent else 65
        lbl = Label(text)
        lbl.style.margin = 8
        lbl.style.margin_bottom = 2
        box.add(lbl)
        box.add(make_label(get_timestamp(), size=10, margin_b=0))
        self.chat_box.add(box)

    def send_message(self, widget):
        text = self.input.value.strip()
        if not text:
            return
        target_label = "desktop" if not self.current_dest else f"{self.current_dest[:12]}..."
        self.add_bubble(f"To {target_label}: {text}", is_sent=True)
        self.input.value = ""
        if self.node and self.node.connected:
            self.node.send_text(self.current_dest, text)
        else:
            self.add_bubble("Not connected to bridge.", is_sent=False)


class ContactsScreen(Box):
    def __init__(self, node):
        super().__init__()
        self.style.direction = COLUMN
        self.style.margin = 10
        self.node = node
        self.add(make_label("Contacts", size=20, margin_b=8))
        announce_btn = Button("Announce Myself", on_press=self.announce)
        self.add(announce_btn)
        self.status = Label("")
        self.add(self.status)
        self.add(make_label("Connected Peers:", size=14, margin_b=6))
        self.peer_label = make_label("(connect to bridge to see peers)")
        self.add(self.peer_label)
        refresh_btn = Button("Refresh", on_press=self.refresh_peers)
        self.add(refresh_btn)

    def announce(self, widget):
        if self.node and self.node.connected:
            self.node.announce()
            self.status.text = "Announced via bridge!"
        else:
            self.status.text = "Not connected"

    def refresh_peers(self, widget):
        if self.node and self.node.connected:
            self.node.send_peers_request()
            self.peer_label.text = "Fetching peers..."
        else:
            self.peer_label.text = "Not connected to bridge"


class NetworkScreen(Box):
    def __init__(self, node):
        super().__init__()
        self.style.direction = COLUMN
        self.style.margin = 10
        self.node = node
        self.add(make_label("Network", size=20, margin_b=8))
        self.add(make_label("Identity:" + (f"\n{node.local_identity[:32]}..." if node else "\nN/A"), size=11, margin_b=12))
        self.status = make_label("")
        self.add(self.status)
        refresh_btn = Button("Refresh", on_press=self.refresh_network)
        self.add(refresh_btn)

    def refresh_network(self, widget):
        if self.node:
            conn = "Bridge: ON" if self.node.connected else "Bridge: OFF"
            self.status.text = conn


class SettingsScreen(Box):
    def __init__(self, node, app_ref):
        super().__init__()
        self.style.direction = COLUMN
        self.style.margin = 10
        self.node = node
        self.app_ref = app_ref

        self.add(make_label("Settings", size=20, margin_b=10))
        self.add(make_label("Desktop Bridge", size=16, margin_b=6))

        row = Box()
        row.style.direction = ROW
        row.style.margin_bottom = 6
        row.add(make_label("Host:", margin_b=0))
        self.host_input = TextInput(placeholder="192.168.1.x")
        self.host_input.style.flex = 1
        row.add(self.host_input)
        self.add(row)

        row2 = Box()
        row2.style.direction = ROW
        row2.style.margin_bottom = 10
        row2.add(make_label("Port:", margin_b=0))
        self.port_input = TextInput(placeholder="4742")
        self.port_input.style.width = 100
        row2.add(self.port_input)
        self.add(row2)

        self.connect_btn = Button("Connect", on_press=self.toggle_connect)
        self.add(self.connect_btn)
        self.status = make_label("")
        self.add(self.status)

        self.add(make_label(f"Identity: {node.local_identity[:16]}...", size=10, margin_b=12))
        self.add(make_label("RMESHV v1.0.0", size=10, margin_b=8))

        try:
            cfg = json.loads((LOCAL_STORE / "bridge.json").read_text()) if (LOCAL_STORE / "bridge.json").exists() else {}
            if "host" in cfg:
                self.host_input.value = cfg["host"]
            if "port" in cfg:
                self.port_input.value = str(cfg["port"])
        except:
            pass

    def toggle_connect(self, widget):
        if not self.node:
            return
        if self.node.connected:
            self.node.disconnect()
            self.status.text = "Disconnected"
            self.connect_btn.text = "Connect"
            return
        host = self.host_input.value.strip()
        port_str = self.port_input.value.strip()
        try:
            port = int(port_str) if port_str else 4742
        except:
            self.status.text = "Invalid port"
            return
        if not host:
            self.status.text = "Enter host IP"
            return
        self.status.text = "Connecting..."
        LOCAL_STORE.mkdir(parents=True, exist_ok=True)
        (LOCAL_STORE / "bridge.json").write_text(json.dumps({"host": host, "port": port}))
        ok = self.node.connect(host, port)
        if ok:
            self.status.text = f"Connected to bridge on {host}:{port}"
            self.connect_btn.text = "Disconnect"
        else:
            self.status.text = f"Connection failed"


class ReticulumMeshApp(App):
    def startup(self):
        self._running = True
        self.main_window = MainWindow(title="RMESHV")
        self.node = BridgeClient()

        self.content_box = Box()
        self.content_box.style.direction = COLUMN
        self.content_box.style.flex = 1

        self.screen_container = Box()
        self.screen_container.style.direction = COLUMN
        self.screen_container.style.flex = 1

        nav_bar = Box()
        nav_bar.style.direction = ROW
        nav_bar.style.margin = 4

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
        if screen_name == "chat":
            screen = MessagesScreen(self, self.node)
        elif screen_name == "contacts":
            screen = ContactsScreen(self.node)
        elif screen_name == "network":
            screen = NetworkScreen(self.node)
        elif screen_name == "settings":
            screen = SettingsScreen(self.node, self)
        else:
            screen = MessagesScreen(self, self.node)
        self.screen_container.add(screen)

    def exit(self):
        self._running = False
        if self.node:
            self.node.disconnect()
        return super().exit()


def main():
    return ReticulumMeshApp()
