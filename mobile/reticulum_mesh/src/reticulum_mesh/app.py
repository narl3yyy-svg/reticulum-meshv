"""RMESHV Mobile - Full mesh client (RNS over TCP + TCP bridge fallback)."""

import os, sys, time, json, socket, threading
from pathlib import Path

_RNS = None
_LXMF = None
try:
    import RNS as _RNS
    try:
        import LXMF as _LXMF
    except:
        pass
except:
    pass

from toga import App, MainWindow, Box, Label, Button, ScrollContainer, TextInput
try:
    from toga.style import Pack
    from toga.constants import COLUMN, ROW
except:
    from toga.style.pack import Pack
    from toga.constants import COLUMN, ROW

C_BG = "#121212"
C_SURFACE = "#1e1e1e"
C_SURFACE2 = "#2a2a2a"
C_ACCENT = "#00bcd4"
C_ACCENT2 = "#448aff"
C_TEXT = "#e0e0e0"
C_TEXT_MUTED = "#9e9e9e"
C_TEXT_DIM = "#616161"
C_BORDER = "#333"
C_BUBBLE_SENT = "#004d40"
C_BUBBLE_RECV = "#263238"
C_SUCCESS = "#69f0ae"
C_WARN = "#ffab40"

LOCAL = Path.home() / ".config" / "rmeshv"


def log(*a):
    m = " ".join(str(x) for x in a)
    try:
        from android import log as al
        al.v("RMESHV", m)
    except:
        print(f"[RM] {m}")


def ts():
    from datetime import datetime
    return datetime.now().strftime("%H:%M")


def ml(text, size=13, color=C_TEXT, bold=False, mb=4):
    l = Label(text)
    l.style.font_size = size
    l.style.color = color
    l.style.font_weight = "bold" if bold else "normal"
    l.style.margin_bottom = mb
    return l


def hrule():
    b = Box()
    b.style.height = 1
    b.style.background_color = C_BORDER
    return b


class MeshConfig:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        try:
            p = LOCAL / "config.json"
            return json.loads(p.read_text()) if p.exists() else {}
        except:
            return {}

    def _save(self):
        LOCAL.mkdir(parents=True, exist_ok=True)
        (LOCAL / "config.json").write_text(json.dumps(self.data, indent=2))

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self._save()


class MeshIdentity:
    def __init__(self):
        self.identity = None
        self.identity_hash = ""
        self.rns_key_path = LOCAL / "rns_identity.key"
        self.fallback_path = LOCAL / "identity_hex.txt"
        self._init()

    def _init(self):
        LOCAL.mkdir(parents=True, exist_ok=True)
        if _RNS:
            self._init_rns()
        else:
            self._init_fallback()

    def _init_rns(self):
        i = None
        if self.rns_key_path.exists():
            try:
                i = _RNS.Identity.from_file(str(self.rns_key_path))
            except:
                pass
        if not i or not i.hash:
            i = _RNS.Identity()
            i.to_file(str(self.rns_key_path))
        self.identity = i
        self.identity_hash = i.hash.hex()

    def _init_fallback(self):
        h = ""
        if self.fallback_path.exists():
            try:
                v = self.fallback_path.read_text().strip()
                if len(v) == 64:
                    h = v
            except:
                pass
        if not h:
            h = os.urandom(32).hex()
            try:
                self.fallback_path.write_text(h)
            except:
                pass
        self.identity_hash = h

    def get_hash(self):
        return self.identity_hash

    def get_rns_identity(self):
        return self.identity

    def has_rns(self):
        return self.identity is not None


class MeshRNS:
    def __init__(self, identity, config):
        self.identity = identity
        self.config = config
        self.reticulum = None
        self.enabled = False
        self.announce_handler_registered = False
        self.discovered_peers = {}
        self.announces = []
        self.interfaces = []
        self._lxmf_router = None
        self._lxmf_source = None
        self.cfg_dir = str(LOCAL / "reticulum")

    def _ensure_config(self, host, port):
        d = Path(self.cfg_dir)
        for s in ["", "storage", "storage/cache", "storage/resources",
                   "storage/identities", "storage/blackhole", "interfaces"]:
            (d / s).mkdir(parents=True, exist_ok=True)
        cfg = d / "config"
        cfg.write_text(f"""[reticulum]
enable_transport = False
share_instance = No
panic_on_interface_error = False

[logging]
loglevel = 3

[interfaces]
  [[RMESHV TCP Link]]
    type = TCPClientInterface
    interface_enabled = Yes
    target_host = {host}
    target_port = {port}
""")

    def enable(self, host, port=4741):
        if _RNS is None:
            return False, "RNS not available"
        if self.enabled:
            return True, "already enabled"
        try:
            self._ensure_config(host, port)
            import signal as _s
            _o = _s.signal
            _s.signal = lambda s, h: None
            try:
                self.reticulum = _RNS.Reticulum(configdir=self.cfg_dir)
            finally:
                _s.signal = _o
            rns_id = self.identity.get_rns_identity()
            if rns_id:
                if not self.announce_handler_registered:
                    try:
                        _RNS.Transport.register_announce_handler(self._on_announce)
                        self.announce_handler_registered = True
                    except:
                        pass
                self._init_lxmf(rns_id)
            self.enabled = True
            self._refresh_interfaces()
            return True, "Reticulum enabled"
        except Exception as e:
            log(f"RNS init fail: {e}")
            return False, str(e)

    def _init_lxmf(self, identity):
        if _LXMF is None:
            return
        try:
            self._lxmf_router = _LXMF.LXMRouter(
                identity=identity,
                storagepath=str(LOCAL / "lxmf")
            )
            self._lxmf_router.register_delivery_identity(
                identity, display_name="RMESHV Mobile"
            )
            self._lxmf_source = _RNS.Destination(
                identity,
                _RNS.Destination.OUT,
                _RNS.Destination.SINGLE,
                "lxmf",
                "delivery"
            )
        except Exception as e:
            log(f"LXMF init fail: {e}")

    def _on_announce(self, dest_hash, announced_identity, app_data):
        if not announced_identity:
            return
        h = dest_hash.hex() if hasattr(dest_hash, 'hex') else dest_hash
        name = (app_data.decode("utf-8", errors="replace") if isinstance(app_data, bytes)
                else str(app_data) if app_data else h[:12])
        n = time.time()
        self.announces.append({"hash": h, "name": name, "time": n})
        self.discovered_peers[h] = {"name": name, "last_seen": n}

    def _refresh_interfaces(self):
        self.interfaces = []
        try:
            for iface in _RNS.Reticulum.interfaces:
                self.interfaces.append({
                    "name": getattr(iface, "name", "?"),
                    "type": type(iface).__name__,
                    "online": getattr(iface, "online", False),
                })
        except:
            pass

    def get_peers(self):
        return list(self.discovered_peers.items())

    def get_announces(self):
        return list(self.announces)

    def get_interfaces(self):
        self._refresh_interfaces()
        return list(self.interfaces)

    def announce(self, display_name=""):
        rns_id = self.identity.get_rns_identity()
        if self.enabled and rns_id:
            try:
                d = _RNS.Destination(rns_id, _RNS.Destination.IN,
                                     _RNS.Destination.SINGLE, "rmeshv", "presence")
                dn = display_name.encode("utf-8") if display_name else None
                d.announce(dn)
                return True
            except Exception as e:
                log(f"announce fail: {e}")
        return False

    def send_text(self, dest_hex, text):
        rns_id = self.identity.get_rns_identity()
        if not self.enabled or not rns_id:
            return False
        try:
            db = bytes.fromhex(dest_hex)
            rid = _RNS.Identity.recall(db)
            if not rid:
                rid = _RNS.Identity()
                rid.hash = db
            if _LXMF and self._lxmf_router and self._lxmf_source:
                dd = _RNS.Destination(rid, _RNS.Destination.OUT,
                                      _RNS.Destination.SINGLE, "lxmf", "delivery")
                dd.set_proof_strategy(_RNS.Destination.PROVE_ALL)
                m = _LXMF.LXMessage(dd, self._lxmf_source,
                                    content=text.encode("utf-8"))
                self._lxmf_router.handle_outbound(m)
            else:
                dd = _RNS.Destination(rid, _RNS.Destination.OUT,
                                      _RNS.Destination.SINGLE, "rmeshv", "msg")
                dd.set_proof_strategy(_RNS.Destination.PROVE_ALL)
                _RNS.Resource(text.encode("utf-8"), dd)
            return True
        except Exception as e:
            log(f"send_text fail: {e}")
            return False

    def disable(self):
        self.enabled = False
        self.reticulum = None


class MeshBridge:
    def __init__(self, identity, config):
        self.identity = identity
        self.config = config
        self.sock = None
        self.running = False
        self.rx_thread = None
        self.messages = {}
        self.discovered_peers = {}
        self._lock = threading.Lock()

    @property
    def connected(self):
        return self.sock is not None and self.running

    def connect(self, host, port):
        self.disconnect()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            s.settimeout(None)
            self.sock = s
            self.running = True
            hello = {"type": "hello", "identity": self.identity.get_hash()}
            rns_id = self.identity.get_rns_identity()
            if rns_id:
                hello["rns_identity"] = rns_id.hash.hex()
            self._send(hello)
            self.rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
            self.rx_thread.start()
            s.settimeout(3)
            try:
                data = b""
                while b"\n" not in data:
                    ch = s.recv(1)
                    if not ch:
                        break
                    data += ch
                if data:
                    msg = json.loads(data.decode().strip())
                    if msg.get("type") == "welcome":
                        pass
            except:
                pass
            s.settimeout(None)
            return True
        except Exception as e:
            log(f"Bridge connect fail: {e}")
            return False

    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None

    def _send(self, data):
        if not self.sock:
            return
        try:
            self.sock.sendall((json.dumps(data) + "\n").encode())
        except:
            self.disconnect()

    def send_message(self, to_hash, text, timestamp=None):
        self._send({
            "type": "message",
            "to": to_hash,
            "text": text,
            "timestamp": timestamp or time.time(),
        })

    def send_announce(self):
        self._send({"type": "announce"})

    def _rx_loop(self):
        buf = b""
        while self.running and self.sock:
            try:
                c = self.sock.recv(4096)
                if not c:
                    break
                buf += c
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        msg = json.loads(line.decode())
                        self._handle(msg)
                    except:
                        pass
            except:
                time.sleep(0.05)
        self.disconnect()

    def _handle(self, msg):
        t = msg.get("type", "")
        if t == "message":
            f = msg.get("from", msg.get("from_hash", "?"))
            tx = msg.get("text", "")
            cid = f
            with self._lock:
                if cid not in self.messages:
                    self.messages[cid] = []
                self.messages[cid].append({"from": cid[:16], "text": tx, "ts": msg.get("timestamp", time.time())})
        elif t == "peers":
            for p in msg.get("peers", []):
                h = p.get("hash", "")
                if h:
                    self.discovered_peers[h] = {"name": p.get("name", h[:12]), "last_seen": time.time()}
        elif t == "announce":
            pass

    def get_messages(self, cid):
        with self._lock:
            return self.messages.pop(cid, [])

    def get_peers(self):
        return list(self.discovered_peers.items())

    def clear_messages(self, cid):
        with self._lock:
            self.messages.pop(cid, None)


# ─── Base screen with dark styling ────────────────────
class DarkBox(Box):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.style.direction = COLUMN
        self.style.flex = 1
        self.style.background_color = C_BG


class PollingMixin:
    """Mixin that provides a persistent daemon poll thread instead of threading.Timer."""

    def start_poll(self, interval, callback):
        self._poll_interval = interval
        self._poll_callback = callback
        self._poll_stop = threading.Event()
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop_poll(self):
        self._poll_stop.set()

    def _poll_loop(self):
        while not self._poll_stop.is_set():
            try:
                self._poll_callback()
            except:
                pass
            self._poll_stop.wait(self._poll_interval)


# ─── Messages ──────────────────────────────────────────
class MessagesScreen(DarkBox, PollingMixin):
    def __init__(self, app_ref, node):
        super().__init__()
        self.style.margin = 6
        self.ar = app_ref
        self.node = node
        self.cdest = ""
        self.add(ml("Messages", size=20, color=C_ACCENT, bold=True, mb=8))

        dr = Box()
        dr.style.direction = ROW
        dr.style.margin_bottom = 4
        tl = Label("To:")
        tl.style.margin_right = 4
        tl.style.color = C_TEXT_MUTED
        tl.style.font_size = 12
        dr.add(tl)
        self.di = TextInput(placeholder="64-char hash (blank=desktop)")
        self.di.style.flex = 1
        dr.add(self.di)
        cb = Button("Chat", on_press=self.start_chat)
        cb.style.width = 60
        cb.style.background_color = C_ACCENT2
        cb.style.color = "#fff"
        cb.style.font_size = 12
        dr.add(cb)
        self.add(dr)

        self.sl = ml("Enter destination or leave blank for desktop.", size=11, color=C_TEXT_MUTED)
        self.add(self.sl)

        sc = ScrollContainer()
        sc.style.flex = 1
        self.cb = Box()
        self.cb.style.direction = COLUMN
        sc.content = self.cb
        self.add(sc)

        ir = Box()
        ir.style.direction = ROW
        ir.style.margin_top = 6
        self.inp = TextInput(placeholder="Type a message...")
        self.inp.style.flex = 1
        self.inp.style.margin_right = 4
        sb = Button("Send", on_press=self.do_send)
        sb.style.width = 60
        sb.style.background_color = C_ACCENT
        sb.style.color = "#fff"
        ir.add(self.inp)
        ir.add(sb)
        self.add(ir)

        self.start_poll(1.0, self._check_incoming)

    def _check_incoming(self):
        if not self.node:
            return
        rns = self.node.rns
        bridge = self.node.bridge
        msgs = {}
        if rns and rns.enabled:
            for cid in list(rns.discovered_peers.keys()):
                pass
        if bridge and bridge.connected:
            for cid, msg_list in list(bridge.messages.items()):
                with bridge._lock:
                    msgs[cid] = bridge.messages.pop(cid, [])
        for cid, mlist in msgs.items():
            if cid == self.cdest or not self.cdest:
                for m in mlist:
                    self.add_bubble(f"[{m['from'][:12]}] {m['text']}", is_sent=False)

    def start_chat(self, widget):
        d = "".join(c for c in self.di.value.strip() if c in "0123456789abcdefABCDEF").lower()
        if len(d) == 64 or not d:
            self.cdest = d
            lbl = "desktop" if not d else f"{d[:12]}..."
            self.add_bubble(f"Chatting with {lbl}", is_sent=False)
            self.sl.text = f"Target: {lbl}"

    def add_bubble(self, text, is_sent=True):
        b = Box()
        b.style.margin = 4
        b.style.margin_left = 50 if is_sent else 4
        b.style.margin_right = 4 if is_sent else 50
        b.style.background_color = C_BUBBLE_SENT if is_sent else C_BUBBLE_RECV
        b.style.border_radius = 8
        l = Label(text)
        l.style.margin = 8
        l.style.color = C_TEXT
        l.style.font_size = 13
        b.add(l)
        l2 = Label(ts())
        l2.style.margin = (0, 8, 4, 8)
        l2.style.color = C_TEXT_MUTED
        l2.style.font_size = 9
        b.add(l2)
        self.cb.add(b)

    def do_send(self, widget):
        t = self.inp.value.strip()
        if not t:
            return
        lbl = "desktop" if not self.cdest else f"{self.cdest[:12]}..."
        self.add_bubble(f"To {lbl}: {t}", is_sent=True)
        self.inp.value = ""
        if not self.node:
            return
        rns = self.node.rns
        bridge = self.node.bridge
        if rns and rns.enabled and self.cdest:
            rns.send_text(self.cdest, t)
        elif bridge and bridge.connected:
            bridge.send_message(self.cdest, t)


# ─── Contacts ──────────────────────────────────────────
class ContactsScreen(DarkBox):
    def __init__(self, node):
        super().__init__()
        self.style.margin = 10
        self.node = node
        self.add(ml("Contacts", size=20, color=C_ACCENT, bold=True, mb=8))
        ab = Button("Announce Myself", on_press=self.do_ann)
        ab.style.background_color = C_SUCCESS
        ab.style.color = "#000"
        ab.style.font_weight = "bold"
        self.add(ab)
        self.st = ml("", size=11, color=C_TEXT_MUTED)
        self.add(self.st)
        self.add(ml("Discovered Peers:", size=14, color=C_ACCENT2, mb=4))
        self.pl = ml("(refresh to see peers)", size=11, color=C_TEXT_MUTED)
        self.add(self.pl)
        rb = Button("Refresh", on_press=self.ref)
        rb.style.background_color = C_SURFACE2
        rb.style.color = C_TEXT
        self.add(rb)
        self.ref(None)

    def do_ann(self, widget):
        if not self.node:
            return
        rns = self.node.rns
        bridge = self.node.bridge
        cfg = self.node.config
        display_name = cfg.get("display_name", "")
        if rns and rns.enabled:
            ok = rns.announce(display_name)
            self.st.text = "Announced via RNS!" if ok else "Failed"
        elif bridge and bridge.connected:
            bridge.send_announce()
            self.st.text = "Announced via bridge!"
        else:
            self.st.text = "Not connected"

    def ref(self, widget):
        if not self.node:
            self.pl.text = "No node"
            return
        peers = {}
        rns = self.node.rns
        bridge = self.node.bridge
        if rns and rns.enabled:
            for h, p in rns.get_peers():
                peers[h] = p
        if bridge and bridge.connected:
            for h, p in bridge.get_peers():
                peers[h] = p
        if peers:
            self.pl.text = "\n".join(f"{h[:12]}... {p['name']}" for h, p in list(peers.items())[:10])
        else:
            self.pl.text = "No peers discovered"
        self.st.text = f"{len(peers)} peer(s)"


# ─── Announces ─────────────────────────────────────────
class AnnouncesScreen(DarkBox, PollingMixin):
    def __init__(self, node):
        super().__init__()
        self.style.margin = 10
        self.node = node
        self.add(ml("Announces", size=20, color=C_ACCENT, bold=True, mb=8))
        self.an_lbl = ml("(no announces yet)", size=11, color=C_TEXT_MUTED)
        self.add(self.an_lbl)
        rb = Button("Refresh", on_press=self.ref)
        rb.style.background_color = C_SURFACE2
        rb.style.color = C_TEXT
        self.add(rb)
        self.start_poll(3.0, self.ref)

    def ref(self, widget=None):
        if not self.node:
            return
        rns = self.node.rns
        ans = rns.get_announces() if rns and rns.enabled else []
        if ans:
            self.an_lbl.text = "\n".join(
                f"{a['name'][:20]}  {a['hash'][:12]}" for a in ans[-10:][::-1]
            )
        else:
            self.an_lbl.text = "No announces yet"


# ─── Interfaces ────────────────────────────────────────
class InterfacesScreen(DarkBox):
    def __init__(self, node):
        super().__init__()
        self.style.margin = 10
        self.node = node
        self.add(ml("Interfaces", size=20, color=C_ACCENT, bold=True, mb=8))
        self.il = ml("(no interfaces)", size=11, color=C_TEXT_MUTED)
        self.add(self.il)
        rb = Button("Refresh", on_press=self.ref)
        rb.style.background_color = C_SURFACE2
        rb.style.color = C_TEXT
        self.add(rb)

    def ref(self, widget):
        if not self.node:
            return
        rns = self.node.rns
        ifaces = rns.get_interfaces() if rns and rns.enabled else []
        if ifaces:
            self.il.text = "\n".join(
                f"{i['name'][:20]}  {i['type'][:15]}  {'ON' if i['online'] else 'OFF'}"
                for i in ifaces
            )
        else:
            self.il.text = "RNS not enabled or no interfaces"


# ─── Network ───────────────────────────────────────────
class NetworkScreen(DarkBox):
    def __init__(self, node):
        super().__init__()
        self.style.margin = 10
        self.node = node
        self.add(ml("Network", size=20, color=C_ACCENT, bold=True, mb=8))
        self.id_lbl = ml("Identity: ", size=11, color=C_TEXT_MUTED)
        self.add(self.id_lbl)
        self.st_lbl = ml("Status: ", size=11, color=C_TEXT_MUTED)
        self.add(self.st_lbl)
        rb = Button("Refresh", on_press=self.ref)
        rb.style.background_color = C_SURFACE2
        rb.style.color = C_TEXT
        self.add(rb)

    def ref(self, widget):
        if not self.node:
            return
        h = self.node.identity.get_hash()
        self.id_lbl.text = f"Identity:\n{h[:32]}..." if h else "Identity:\nN/A"
        rns = self.node.rns
        bridge = self.node.bridge
        if rns and rns.enabled:
            self.st_lbl.text = f"RNS: ON | Peers: {len(rns.get_peers())}"
        elif bridge and bridge.connected:
            self.st_lbl.text = "Bridge: connected"
        else:
            self.st_lbl.text = "Not connected"


# ─── Settings ──────────────────────────────────────────
class SettingsScreen(DarkBox):
    def __init__(self, node, app_ref):
        super().__init__()
        self.style.margin = 10
        self.node = node
        self.ar = app_ref
        self.add(ml("Settings", size=20, color=C_ACCENT, bold=True, mb=10))

        self.add(ml("Desktop Bridge / TCP Link", size=14, color=C_ACCENT2, mb=4))

        r1 = Box()
        r1.style.direction = ROW
        r1.style.margin_bottom = 4
        hl = Label("Host:")
        hl.style.margin_right = 4
        hl.style.color = C_TEXT
        hl.style.font_size = 12
        r1.add(hl)
        self.hi = TextInput(placeholder="192.168.1.x")
        self.hi.style.flex = 1
        r1.add(self.hi)
        self.add(r1)

        r2 = Box()
        r2.style.direction = ROW
        r2.style.margin_bottom = 8
        pl = Label("Port:")
        pl.style.margin_right = 4
        pl.style.color = C_TEXT
        pl.style.font_size = 12
        r2.add(pl)
        self.pi = TextInput(placeholder="4741")
        self.pi.style.width = 80
        r2.add(self.pi)
        self.add(r2)

        self.cb = Button("Connect (RNS via TCP)", on_press=self.do_rns)
        self.cb.style.background_color = C_ACCENT
        self.cb.style.color = "#fff"
        self.cb.style.font_weight = "bold"
        self.add(self.cb)

        self.fb = Button("Connect (TCP Bridge)", on_press=self.do_bridge)
        self.fb.style.background_color = C_SURFACE2
        self.fb.style.color = C_TEXT
        self.add(self.fb)

        self.st = ml("", size=11, color=C_WARN)
        self.add(self.st)

        self.add(hrule())

        self.add(ml(f"ID: {self.node.identity.get_hash()[:16]}...", size=10, color=C_TEXT_DIM, mb=4))
        self.add(ml("RMESHV v1.0.0", size=10, color=C_TEXT_DIM))
        self.add(ml("Reticulum " + (getattr(_RNS, "__version__", "?") if _RNS else "N/A"),
                     size=9, color=C_TEXT_DIM))

        c = self.node.config.data
        if c.get("host"):
            self.hi.value = c["host"]
        if c.get("port"):
            self.pi.value = str(c["port"])
        if not self.pi.value:
            self.pi.value = "4741"

    def do_rns(self, widget):
        host = self.hi.value.strip()
        port_s = self.pi.value.strip()
        try:
            port = int(port_s) if port_s else 4741
        except:
            self.st.text = "Invalid port"
            return
        if not host:
            self.st.text = "Enter host IP"
            return
        self.st.text = "Starting RNS over TCP..."
        self.node.config.set("host", host)
        self.node.config.set("port", port)
        self.node.config.set("mode", "rns")
        bridge = self.node.bridge
        if bridge and bridge.connected:
            bridge.disconnect()
        rns = self.node.rns
        ok, msg = rns.enable(host, port)
        if ok:
            self.st.text = f"RNS enabled! via {host}:{port}"
            self.st.color = C_SUCCESS
            rns.announce(self.node.config.get("display_name", ""))
        else:
            self.st.text = f"RNS failed: {msg}"
            self.st.color = C_WARN

    def do_bridge(self, widget):
        host = self.hi.value.strip()
        port_s = self.pi.value.strip()
        try:
            port = int(port_s) if port_s else 4742
        except:
            self.st.text = "Invalid port"
            return
        if not host:
            self.st.text = "Enter host IP"
            return
        self.st.text = "Connecting bridge..."
        self.node.config.set("host", host)
        self.node.config.set("port", port)
        self.node.config.set("mode", "bridge")
        bridge = self.node.bridge
        ok = bridge.connect(host, port)
        if ok:
            self.st.text = f"Bridge connected! {host}:{port}"
            self.st.color = C_SUCCESS
        else:
            self.st.text = "Bridge connection failed"
            self.st.color = C_WARN


# ─── Background worker ─────────────────────────────────
class BackgroundWorker:
    """Single background thread for bridge reconnection and periodic announces."""

    def __init__(self, node):
        self.node = node
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            try:
                node = self.node
                config = node.config
                bridge = node.bridge

                auto_mode = config.get("mode", "")
                auto_host = config.get("host", "")
                auto_port = config.get("port", "")

                if auto_mode == "bridge" and auto_host:
                    rns = node.rns
                    if not bridge.connected and not (rns and rns.enabled):
                        port = auto_port if auto_port else 4742
                        try:
                            port = int(port)
                        except:
                            port = 4742
                        log(f"Auto-reconnect bridge to {auto_host}:{port}")
                        bridge.connect(auto_host, port)

                if bridge.connected:
                    bridge.send_announce()
            except:
                pass
            self._stop.wait(30)


# ─── Main App ──────────────────────────────────────────
class ReticulumMeshApp(App):
    def startup(self):
        self._running = True
        self.main_window = MainWindow(title="RMESHV")
        self.main_window.style.background_color = C_BG

        self.config = MeshConfig()
        self.identity = MeshIdentity()
        self.rns = MeshRNS(self.identity, self.config)
        self.bridge = MeshBridge(self.identity, self.config)

        self.node = self  # backwards compat for screens that reference self.node

        self.worker = BackgroundWorker(self)

        auto_mode = self.config.get("mode", "")
        auto_host = self.config.get("host", "")
        auto_port = self.config.get("port", "")

        if auto_mode == "rns" and auto_host:
            try:
                port = int(auto_port) if auto_port else 4741
            except:
                port = 4741
            log(f"Auto-connect RNS to {auto_host}:{port}")
            self.rns.enable(auto_host, port)
        elif auto_mode == "bridge" and auto_host:
            try:
                port = int(auto_port) if auto_port else 4742
            except:
                port = 4742
            log(f"Auto-connect bridge to {auto_host}:{port}")
            self.bridge.connect(auto_host, port)

        self.content = Box()
        self.content.style.direction = COLUMN
        self.content.style.flex = 1

        self.sc = Box()
        self.sc.style.direction = COLUMN
        self.sc.style.flex = 1

        nb = Box()
        nb.style.direction = ROW
        nb.style.background_color = C_SURFACE
        nb.style.padding = 2

        for name, key in [("Chat", "chat"), ("Contacts", "cnt"),
                          ("Ann", "ann"), ("IFace", "iface"),
                          ("Net", "net"), ("Settings", "set")]:
            b = Button(name, on_press=lambda w, k=key: self.ss(k))
            b.style.flex = 1
            b.style.font_size = 10
            b.style.color = C_TEXT
            b.style.background_color = C_SURFACE
            nb.add(b)

        self.content.add(self.sc)
        self.content.add(nb)
        self.main_window.content = self.content
        self.main_window.show()
        self.ss("chat")

        if self.rns.enabled:
            self.rns.announce(self.config.get("display_name", ""))

    def ss(self, name):
        self.sc.clear()
        m = {
            "chat": lambda: MessagesScreen(self, self),
            "cnt": lambda: ContactsScreen(self),
            "ann": lambda: AnnouncesScreen(self),
            "iface": lambda: InterfacesScreen(self),
            "net": lambda: NetworkScreen(self),
            "set": lambda: SettingsScreen(self, self),
        }
        s = m.get(name, lambda: MessagesScreen(self, self))()
        self.sc.add(s)

    def exit(self):
        self._running = False
        if self.bridge:
            self.bridge.disconnect()
        if self.worker:
            self.worker.stop()
        return super().exit()


def main():
    return ReticulumMeshApp()
