"""RMESHV Mobile — RNS + LXMF messaging client for Android."""

import os
import sys
import time
import json
import threading
from pathlib import Path

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.listview import ListView, ListItemButton
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, ListProperty, ObjectProperty

# RNS + LXMF
import RNS
import LXMF

# Storage paths
APP_DIR = Path(os.environ.get("ANDROID_APP_PATH", str(Path.home() / ".config" / "rmeshv")))
APP_DIR.mkdir(parents=True, exist_ok=True)
RNS_CONFIG_DIR = APP_DIR / "rns_config"
RNS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LXMF_STORAGE_DIR = APP_DIR / "lxmf"
LXMF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR = APP_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def create_rns_config():
    config_path = RNS_CONFIG_DIR / "config"
    if not config_path.exists():
        config_path.write_text("""# Reticulum configuration for RMESHV Mobile

[reticulum]
  enable_transport = No
  share_instance = Yes

[[AutoInterface]]
  type = AutoInterface
  interface_enabled = Yes
""")


class MeshBackend:
    def __init__(self):
        self.identity = None
        self.reticulum = None
        self.lxmf_messenger = None
        self.network_monitor = None
        self.peers = {}
        self.conversations = {}
        self.display_name = ""
        self.message_callback = None
        self.peer_callback = None
        self._load_config()
        self._init_rns()

    def _config_path(self):
        return APP_DIR / "config.json"

    def _load_config(self):
        path = self._config_path()
        if path.exists():
            try:
                self.config = json.loads(path.read_text())
            except:
                self.config = {}
        else:
            self.config = {"display_name": "", "server_host": "", "server_port": "4242"}

        self.display_name = self.config.get("display_name", "")

    def _save_config(self):
        self._config_path().write_text(json.dumps(self.config, indent=2))

    def set_display_name(self, name):
        self.display_name = name
        self.config["display_name"] = name
        self._save_config()
        if self.lxmf_messenger:
            self.lxmf_messenger.set_display_name(name)

    def get_server_host(self):
        return self.config.get("server_host", "")

    def set_server_host(self, host):
        self.config["server_host"] = host
        self._save_config()

    def get_server_port(self):
        return self.config.get("server_port", "4242")

    def set_server_port(self, port):
        self.config["server_port"] = port
        self._save_config()

    def _init_rns(self):
        try:
            create_rns_config()
            self.reticulum = RNS.Reticulum(configdir=str(RNS_CONFIG_DIR))
            self.identity = self._load_or_create_identity()

            if self.identity:
                self.lxmf_messenger = LXMFMessenger(
                    self.identity,
                    storage_dir=str(LXMF_STORAGE_DIR),
                    display_name=self.display_name or "RMESHV User"
                )
                self.lxmf_messenger.set_message_callback(self._on_message)

                # Register announce handler
                class AnnounceHandler:
                    aspect_filter = None
                    def __init__(self, callback):
                        self._callback = callback
                    def received_announce(self, destination_hash, announced_identity, app_data, announce_packet_hash=None):
                        try:
                            self._callback(destination_hash, announced_identity, app_data)
                        except:
                            pass

                try:
                    handler = AnnounceHandler(self._on_announce)
                    RNS.Transport.register_announce_handler(handler)
                except:
                    pass

                self._load_history()
                print(f"[RMESHV] RNS ready. Identity: {self.get_identity_hash()[:16]}...")
                print(f"[RMESHV] LXMF delivery hash: {self.lxmf_messenger.delivery_dest.hash.hex()[:16]}...")

        except Exception as e:
            print(f"[RMESHV] Init error: {e}")
            import traceback
            traceback.print_exc()

    def _load_or_create_identity(self):
        identity_path = APP_DIR / "identity.key"
        if identity_path.exists():
            try:
                identity = RNS.Identity.from_file(str(identity_path))
                if identity and getattr(identity, "hash", None):
                    return identity
            except:
                pass
        identity = RNS.Identity()
        identity.to_file(str(identity_path))
        return identity

    def get_identity_hash(self):
        if not self.identity:
            return ""
        try:
            return self.identity.hash.hex()
        except:
            return ""

    def get_lxmf_hash(self):
        if self.lxmf_messenger and self.lxmf_messenger.delivery_dest:
            return self.lxmf_messenger.delivery_dest.hash.hex()
        return ""

    def _on_message(self, sender_hash, content, title, timestamp):
        print(f"[RMESHV] Message from {sender_hash[:16]}...: {content[:50]}")
        if sender_hash not in self.conversations:
            self.conversations[sender_hash] = []
        self.conversations[sender_hash].append({
            "sender": sender_hash,
            "content": content,
            "title": title,
            "timestamp": timestamp,
            "is_outgoing": False,
        })
        self._save_history(sender_hash)
        if self.message_callback:
            self.message_callback(sender_hash, content, title, timestamp)

    def _on_announce(self, destination_hash, announced_identity, app_data):
        if not announced_identity:
            return
        hash_hex = destination_hash.hex() if hasattr(destination_hash, 'hex') else str(destination_hash)

        # Decode app_data (LXMF uses msgpack [display_name, stamp_cost, features])
        name = ""
        if app_data:
            if isinstance(app_data, bytes):
                try:
                    import msgpack
                    unpacked = msgpack.unpackb(app_data, raw=False)
                    if isinstance(unpacked, (list, tuple)) and len(unpacked) >= 1:
                        n = unpacked[0]
                        if isinstance(n, bytes):
                            name = n.decode("utf-8", errors="replace")
                        elif isinstance(n, str):
                            name = n
                except:
                    try:
                        name = app_data.decode("utf-8", errors="replace")
                    except:
                        name = hash_hex[:12]
            else:
                name = str(app_data)

        self.peers[hash_hex] = {
            "hash": hash_hex,
            "name": name or hash_hex[:12],
            "last_seen": time.time(),
        }
        print(f"[RMESHV] Announce: {name} ({hash_hex[:16]}...)")
        if self.peer_callback:
            self.peer_callback()

    def send_message(self, dest_hash, text):
        if self.lxmf_messenger:
            result = self.lxmf_messenger.send_message(dest_hash, text)
            if result:
                if dest_hash not in self.conversations:
                    self.conversations[dest_hash] = []
                self.conversations[dest_hash].append({
                    "sender": self.get_identity_hash(),
                    "content": text,
                    "timestamp": time.time(),
                    "is_outgoing": True,
                })
                self._save_history(dest_hash)
            return result
        return False

    def announce(self):
        if self.lxmf_messenger:
            name = self.display_name or "RMESHV User"
            return self.lxmf_messenger.announce(name)
        return False

    def connect_to_server(self, host, port):
        if not host:
            return False
        try:
            config_path = RNS_CONFIG_DIR / "config"
            text = config_path.read_text() if config_path.exists() else ""
            if f"target_host = {host}" in text:
                return True
            entry = f"\n[[TCP Client {host}]]\n  type = TCPClientInterface\n  interface_enabled = Yes\n  target_host = {host}\n  target_port = {port}\n"
            config_path.write_text(text.rstrip() + "\n" + entry)
            print(f"[RMESHV] Added TCP client to {host}:{port}")
            return True
        except Exception as e:
            print(f"[RMESHV] Connect error: {e}")
            return False

    def get_peers(self):
        return list(self.peers.values())

    def get_conversations(self):
        return dict(self.conversations)

    def get_conversation(self, peer_hash):
        return self.conversations.get(peer_hash, [])

    def _history_path(self, peer_hash):
        safe = peer_hash.replace("/", "_").replace("\\", "_")
        return HISTORY_DIR / f"{safe}.json"

    def _save_history(self, peer_hash):
        try:
            msgs = self.conversations.get(peer_hash, [])
            self._history_path(peer_hash).write_text(json.dumps(msgs, indent=2))
        except:
            pass

    def _load_history(self):
        for f in HISTORY_DIR.glob("*.json"):
            try:
                peer_hash = f.stem
                msgs = json.loads(f.read_text())
                if isinstance(msgs, list):
                    self.conversations[peer_hash] = msgs
            except:
                pass


class LXMFMessenger:
    def __init__(self, identity, storage_dir, display_name="RMESHV User"):
        self.identity = identity
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.display_name = display_name

        self.router = LXMF.LXMRouter(
            identity=identity,
            storagepath=str(self.storage_dir),
        )

        self.delivery_dest = self.router.register_delivery_identity(
            identity, display_name=display_name
        )
        self.delivery_dest.set_proof_strategy(RNS.Destination.PROVE_ALL)
        self.router.register_delivery_callback(self._on_message)

        self.message_callback = None

    def set_display_name(self, name):
        self.display_name = name
        try:
            if self.delivery_dest:
                self.delivery_dest.display_name = name
        except:
            pass

    def _on_message(self, lxmessage):
        try:
            source_hash = ""
            if lxmessage.source and hasattr(lxmessage.source, 'hash'):
                source_hash = lxmessage.source.hash.hex()
            elif hasattr(lxmessage, 'source_hash') and lxmessage.source_hash:
                source_hash = lxmessage.source_hash.hex() if isinstance(lxmessage.source_hash, bytes) else str(lxmessage.source_hash)

            content = ""
            if lxmessage.content:
                content = lxmessage.content.decode("utf-8", errors="replace")

            title = ""
            if lxmessage.title:
                try:
                    title = lxmessage.title.decode("utf-8", errors="replace") if isinstance(lxmessage.title, bytes) else str(lxmessage.title)
                except:
                    pass

            timestamp = getattr(lxmessage, "timestamp", None) or time.time()

            # Check for file attachments
            try:
                fields = lxmessage.get_fields()
                if LXMF.FIELD_FILE_ATTACHMENTS in fields:
                    for att in fields[LXMF.FIELD_FILE_ATTACHMENTS]:
                        if isinstance(att, (list, tuple)) and len(att) >= 2:
                            fname = att[0]
                            fdata = att[1]
                            if isinstance(fdata, (bytes, bytearray)):
                                downloads = Path.home() / "Downloads" / "RMESHV"
                                downloads.mkdir(parents=True, exist_ok=True)
                                fpath = downloads / (fname if isinstance(fname, str) else fname.decode("utf-8", errors="replace"))
                                with open(fpath, "wb") as f:
                                    f.write(fdata)
                                print(f"[RMESHV] Saved file: {fpath}")
            except:
                pass

            if self.message_callback:
                self.message_callback(source_hash, content, title, timestamp)

        except Exception as e:
            print(f"[RMESHV] Message error: {e}")

    def send_message(self, destination_hash, text, title="", file_path=None):
        try:
            dest_bytes = bytes.fromhex(destination_hash)
            remote_identity = RNS.Identity.recall(dest_bytes)
            if not remote_identity:
                remote_identity = RNS.Identity()
                remote_identity.hash = dest_bytes

            dest = RNS.Destination(
                remote_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                "lxmf",
                "delivery"
            )

            fields = {}
            if file_path:
                import os
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                fname = os.path.basename(file_path)
                fields[LXMF.FIELD_FILE_ATTACHMENTS] = [(fname, file_data)]
                if not text:
                    text = f"[File: {fname}]"

            message = LXMF.LXMessage(
                dest,
                self.delivery_dest,
                content=text.encode("utf-8") if isinstance(text, str) else text,
                title=title.encode("utf-8") if title else b"",
                fields=fields if fields else None,
            )
            message.desired_method = LXMF.LXMessage.DIRECT

            self.router.handle_outbound(message)
            print(f"[RMESHV] Sent to {destination_hash[:16]}...: {text[:50]}")
            return True
        except Exception as e:
            print(f"[RMESHV] Send error: {e}")
            return False

    def announce(self, app_data=""):
        try:
            name = app_data if app_data else self.display_name
            if self.delivery_dest:
                self.delivery_dest.display_name = name
            if self.router:
                self.router.announce(destination_hash=self.delivery_dest.hash)
                print(f"[RMESHV] Announced as: {name}")
                return True
        except Exception as e:
            print(f"[RMESHV] Announce error: {e}")
        return False


# === Kivy UI ===

class MessageBubble(BoxLayout):
    def __init__(self, text, is_self, timestamp, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = [dp(10), dp(5)]

        if is_self:
            self.canvas.clear()
            with self.canvas.before:
                Color(0.15, 0.35, 0.6, 1)
                Rectangle(pos=self.pos, size=self.size)
            label = Label(text=text, color=(1, 1, 1, 1), size_hint_y=None, height=dp(40),
                         halign='left', valign='middle', text_size=(None, dp(40)))
        else:
            self.canvas.clear()
            with self.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                Rectangle(pos=self.pos, size=self.size)
            label = Label(text=text, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=dp(40),
                         halign='left', valign='middle', text_size=(None, dp(40)))

        self.bind(pos=self._update_rect, size=self._update_rect)
        self.add_widget(label)

    def _update_rect(self, instance, value):
        self.canvas.before.children[1].pos = instance.pos
        self.canvas.before.children[1].size = instance.size


class ConversationItem(BoxLayout):
    def __init__(self, peer_hash, name, last_msg, on_select, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(60)
        self.peer_hash = peer_hash

        info = BoxLayout(orientation='vertical')
        info.add_widget(Label(text=name, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=dp(30),
                             halign='left', valign='middle', text_size=(None, dp(30))))
        info.add_widget(Label(text=last_msg[:40], color=(0.6, 0.6, 0.6, 1), size_hint_y=None, height=dp(25),
                             halign='left', valign='middle', text_size=(None, dp(25)), font_size='12sp'))
        self.add_widget(info)

        btn = Button(text='>', size_hint_x=0.2, background_color=(0.15, 0.35, 0.6, 1))
        btn.bind(on_release=lambda x: on_select(peer_hash, name))
        self.add_widget(btn)


class RMESHVApp(App):
    def build(self):
        self.backend = MeshBackend()
        self.current_conv = None

        # Dark theme
        from kivy.core.window import Window
        Window.clearcolor = (0.07, 0.07, 0.07, 1)

        # Main layout
        self.root = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        with header.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(header.canvas.before.children[1], 'pos', v),
                    size=lambda i, v: setattr(header.canvas.before.children[1], 'size', v))

        self.title_label = Label(text='RMESHV', color=(0.25, 0.55, 0.95, 1), bold=True, font_size='20sp')
        header.add_widget(self.title_label)

        announce_btn = Button(text='Announce', size_hint_x=0.3, background_color=(0.15, 0.35, 0.6, 1))
        announce_btn.bind(on_release=self._announce)
        header.add_widget(announce_btn)

        self.root.add_widget(header)

        # Tabs
        self.tabs = TabbedPanel(do_default_tab=False)

        # Messages tab
        msg_tab = TabbedPanelItem(text='Messages')
        self._build_messages_tab(msg_tab)
        self.tabs.add_widget(msg_tab)

        # Peers tab
        peers_tab = TabbedPanelItem(text='Peers')
        self._build_peers_tab(peers_tab)
        self.tabs.add_widget(peers_tab)

        # Settings tab
        settings_tab = TabbedPanelItem(text='Settings')
        self._build_settings_tab(settings_tab)
        self.tabs.add_widget(settings_tab)

        self.root.add_widget(self.tabs)

        # Set callbacks
        self.backend.message_callback = self._on_message
        self.backend.peer_callback = self._refresh_peers

        # Schedule periodic refresh
        Clock.schedule_interval(self._periodic_refresh, 5)

        return self.root

    def _build_messages_tab(self, tab):
        layout = BoxLayout(orientation='vertical')

        # Conversation list
        self.conv_scroll = ScrollView(size_hint_y=0.4)
        self.conv_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.conv_list.bind(minimum_height=self.conv_list.setter('height'))
        self.conv_scroll.add_widget(self.conv_list)
        layout.add_widget(self.conv_scroll)

        # Chat view
        self.chat_label = Label(text='Select a conversation', color=(0.5, 0.5, 0.5, 1), size_hint_y=0.05)
        layout.add_widget(self.chat_label)

        self.chat_scroll = ScrollView()
        self.chat_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.chat_list.bind(minimum_height=self.chat_list.setter('height'))
        self.chat_scroll.add_widget(self.chat_list)
        layout.add_widget(self.chat_scroll)

        # Input
        input_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45))
        self.msg_input = TextInput(hint_text='Type a message...', multiline=False,
                                   background_color=(0.15, 0.15, 0.15, 1),
                                   foreground_color=(0.9, 0.9, 0.9, 1))
        input_row.add_widget(self.msg_input)

        send_btn = Button(text='Send', size_hint_x=0.3, background_color=(0.15, 0.35, 0.6, 1))
        send_btn.bind(on_release=self._send_message)
        input_row.add_widget(send_btn)

        layout.add_widget(input_row)
        tab.add_widget(layout)

    def _build_peers_tab(self, tab):
        layout = BoxLayout(orientation='vertical')

        self.peers_scroll = ScrollView()
        self.peers_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.peers_list.bind(minimum_height=self.peers_list.setter('height'))
        self.peers_scroll.add_widget(self.peers_list)
        layout.add_widget(self.peers_scroll)

        refresh_btn = Button(text='Refresh', size_hint_y=None, height=dp(45),
                            background_color=(0.15, 0.35, 0.6, 1))
        refresh_btn.bind(on_release=lambda x: self._refresh_peers())
        layout.add_widget(refresh_btn)

        tab.add_widget(layout)

    def _build_settings_tab(self, tab):
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=[dp(20), dp(20)])

        # Display name
        layout.add_widget(Label(text='Display Name', color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=dp(30)))
        self.name_input = TextInput(text=self.backend.display_name, multiline=False,
                                    background_color=(0.15, 0.15, 0.15, 1),
                                    foreground_color=(0.9, 0.9, 0.9, 1),
                                    size_hint_y=None, height=dp(40))
        layout.add_widget(self.name_input)

        save_name_btn = Button(text='Save Name', size_hint_y=None, height=dp(45),
                              background_color=(0.15, 0.35, 0.6, 1))
        save_name_btn.bind(on_release=self._save_name)
        layout.add_widget(save_name_btn)

        # Separator
        layout.add_widget(Label(text='', size_hint_y=None, height=dp(20)))

        # Server connection
        layout.add_widget(Label(text='Connect to Desktop Server', color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=dp(30)))
        layout.add_widget(Label(text='Enter the IP of your desktop running RMESHV:', color=(0.6, 0.6, 0.6, 1),
                               size_hint_y=None, height=dp(25), font_size='12sp'))

        self.host_input = TextInput(hint_text='Server IP (e.g. 10.10.100.12)',
                                    text=self.backend.get_server_host(),
                                    multiline=False,
                                    background_color=(0.15, 0.15, 0.15, 1),
                                    foreground_color=(0.9, 0.9, 0.9, 1),
                                    size_hint_y=None, height=dp(40))
        layout.add_widget(self.host_input)

        self.port_input = TextInput(hint_text='Port', text=self.backend.get_server_port(),
                                    multiline=False,
                                    background_color=(0.15, 0.15, 0.15, 1),
                                    foreground_color=(0.9, 0.9, 0.9, 1),
                                    size_hint_y=None, height=dp(40))
        layout.add_widget(self.port_input)

        connect_btn = Button(text='Connect to Server', size_hint_y=None, height=dp(45),
                            background_color=(0.15, 0.35, 0.6, 1))
        connect_btn.bind(on_release=self._connect_server)
        layout.add_widget(connect_btn)

        # Separator
        layout.add_widget(Label(text='', size_hint_y=None, height=dp(20)))

        # Identity info
        self.id_label = Label(text=f'Identity: {self.backend.get_identity_hash()[:20]}...',
                             color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(30),
                             font_size='11sp')
        layout.add_widget(self.id_label)

        self.lxmf_label = Label(text=f'LXMF: {self.backend.get_lxmf_hash()[:20]}...',
                               color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(30),
                               font_size='11sp')
        layout.add_widget(self.lxmf_label)

        tab.add_widget(layout)

    def _refresh_conversations(self):
        self.conv_list.clear_widgets()
        convs = self.backend.get_conversations()
        for peer_hash, messages in convs.items():
            name = peer_hash[:12]
            last_msg = messages[-1]["content"][:40] if messages else "No messages"
            item = ConversationItem(peer_hash, name, last_msg, self._select_conversation)
            self.conv_list.add_widget(item)

    def _refresh_peers(self):
        self.peers_list.clear_widgets()
        peers = self.backend.get_peers()
        for peer in peers:
            name = peer.get("name", peer["hash"][:12])
            hash_str = peer["hash"][:16] + "..."

            item = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(70))
            item.add_widget(Label(text=name, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=dp(25),
                                 halign='left', font_size='14sp'))
            item.add_widget(Label(text=hash_str, color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(20),
                                 halign='left', font_size='11sp'))

            btn = Button(text='Message', size_hint_y=None, height=dp(35),
                        background_color=(0.15, 0.35, 0.6, 1))
            btn.bind(on_release=lambda x, h=peer["hash"], n=name: self._start_conversation(h, n))
            item.add_widget(btn)

            self.peers_list.add_widget(item)

        if not peers:
            self.peers_list.add_widget(Label(text='No peers discovered yet.\nAnnounce and wait for others.',
                                            color=(0.5, 0.5, 0.5, 1)))

    def _select_conversation(self, peer_hash, name):
        self.current_conv = peer_hash
        self.chat_label.text = name
        self._load_chat_messages(peer_hash)

    def _start_conversation(self, peer_hash, name):
        self._select_conversation(peer_hash, name)
        self.tabs.switch_to(self.tabs.tab_list[0])

    def _load_chat_messages(self, peer_hash):
        self.chat_list.clear_widgets()
        messages = self.backend.get_conversation(peer_hash)
        my_hash = self.backend.get_identity_hash()
        for msg in messages:
            is_self = msg.get("is_outgoing", False) or msg.get("sender", "") == my_hash
            content = msg.get("content", "")
            bubble = MessageBubble(content, is_self, msg.get("timestamp", 0))
            self.chat_list.add_widget(bubble)

    def _send_message(self, instance):
        text = self.msg_input.text.strip()
        if not text or not self.current_conv:
            return
        self.backend.send_message(self.current_conv, text)
        self.msg_input.text = ''
        self._load_chat_messages(self.current_conv)
        self._refresh_conversations()

    def _on_message(self, sender_hash, content, title, timestamp):
        Clock.schedule_once(lambda dt: self._handle_incoming(sender_hash, content), 0)

    def _handle_incoming(self, sender_hash, content):
        self._refresh_conversations()
        if self.current_conv == sender_hash:
            self._load_chat_messages(sender_hash)

    def _announce(self, instance):
        name = self.backend.display_name or "RMESHV User"
        self.backend.announce()
        popup = Popup(title='Announced', content=Label(text=f'Announced as: {name}'),
                     size_hint=(0.8, 0.3))
        popup.open()

    def _save_name(self, instance):
        name = self.name_input.text.strip()
        if name:
            self.backend.set_display_name(name)
            popup = Popup(title='Saved', content=Label(text=f'Display name: {name}'),
                         size_hint=(0.8, 0.3))
            popup.open()

    def _connect_server(self, instance):
        host = self.host_input.text.strip()
        port = self.port_input.text.strip() or "4242"
        if host:
            self.backend.set_server_host(host)
            self.backend.set_server_port(port)
            result = self.backend.connect_to_server(host, port)
            if result:
                popup = Popup(title='Added',
                             content=Label(text=f'TCP client to {host}:{port} added.\nRestart app to apply.'),
                             size_hint=(0.8, 0.4))
            else:
                popup = Popup(title='Error',
                             content=Label(text='Failed to add connection.'),
                             size_hint=(0.8, 0.3))
            popup.open()

    def _periodic_refresh(self, dt):
        self._refresh_peers()
        self._refresh_conversations()
        self.id_label.text = f'Identity: {self.backend.get_identity_hash()[:20]}...'
        self.lxmf_label.text = f'LXMF: {self.backend.get_lxmf_hash()[:20]}...'


def main():
    return RMESHVApp().run()


if __name__ == '__main__':
    main()
