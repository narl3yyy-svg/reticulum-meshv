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


class MeshNode:
    def __init__(self):
        self.reticulum = None
        self.identity = None
        self.identity_hash = ""
        self.rns_enabled = False
        self.discovered_peers = {}
        self.announces = []
        self.interfaces = []
        self.messages = {}
        self.config = self._lj("config.json", {"host": "", "port": 4741, "mode": "rns"})
        self.cfg_dir = str(LOCAL / "reticulum")
        self._ann_h = False
        self.bridge = None
        self._init_id()

    def _lj(self, name, default):
        try:
            p = LOCAL / name
            return json.loads(p.read_text()) if p.exists() else default
        except:
            return default

    def _sj(self, name, data):
        LOCAL.mkdir(parents=True, exist_ok=True)
        (LOCAL / name).write_text(json.dumps(data, indent=2))

    def _init_id(self):
        LOCAL.mkdir(parents=True, exist_ok=True)
        p = LOCAL / "identity.txt"
        if p.exists():
            try:
                v = p.read_text().strip()
                if len(v) == 64:
                    self.identity_hash = v
                    return
            except:
                pass
        self.identity_hash = os.urandom(32).hex()
        try:
            p.write_text(self.identity_hash)
        except:
            pass

    def _ensure_cfg(self, host, port):
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

    def enable_rns(self, host, port=4741):
        if _RNS is None:
            return False, "RNS not available"
        if self.rns_enabled:
            return True, "already enabled"
        try:
            self._ensure_cfg(host, port)
            self.cfg_dir = str(LOCAL / "reticulum")
            import signal as _s
            _o = _s.signal
            _s.signal = lambda s, h: None
            try:
                self.reticulum = _RNS.Reticulum(configdir=self.cfg_dir)
            finally:
                _s.signal = _o
            self.identity = self._load_rns_id()
            if self.identity:
                self.identity_hash = self.identity.hash.hex()
            if not self._ann_h:
                try:
                    _RNS.Transport.register_announce_handler(self._on_ann)
                    self._ann_h = True
                except:
                    pass
            self.rns_enabled = True
            self._ri()
            return True, "Reticulum enabled"
        except Exception as e:
            log(f"RNS init fail: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)

    def _load_rns_id(self):
        p = LOCAL / "rns_identity.key"
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            try:
                i = _RNS.Identity.from_file(str(p))
                if i and i.hash:
                    return i
            except:
                pass
            try:
                p.unlink(missing_ok=True)
            except:
                pass
        i = _RNS.Identity()
        i.to_file(str(p))
        return i

    def _on_ann(self, dest_hash, announced_identity, app_data):
        if not announced_identity:
            return
        h = dest_hash.hex() if hasattr(dest_hash, 'hex') else dest_hash
        name = (app_data.decode("utf-8", errors="replace") if isinstance(app_data, bytes)
                else str(app_data) if app_data else h[:12])
        n = time.time()
        self.announces.append({"hash": h, "name": name, "time": n})
        self.discovered_peers[h] = {"name": name, "last_seen": n}

    def _ri(self):
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

    def announce(self):
        if self.rns_enabled and self.identity:
            try:
                d = _RNS.Destination(self.identity, _RNS.Destination.IN,
                                     _RNS.Destination.SINGLE, "rmeshv", "presence")
                dn = self.config.get("display_name", "").encode("utf-8")
                d.announce(dn)
                return True
            except Exception as e:
                log(f"announce fail: {e}")
        return False

    def send_text(self, dest_hex, text):
        if not self.rns_enabled or not self.identity:
            return False
        try:
            db = bytes.fromhex(dest_hex)
            rid = _RNS.Identity.recall(db)
            if not rid:
                rid = _RNS.Identity()
                rid.hash = db
            if _LXMF:
                r = _LXMF.LXMRouter(identity=self.identity)
                dd = _RNS.Destination(rid, _RNS.Destination.OUT,
                                      _RNS.Destination.SINGLE, "lxmf", "delivery")
                m = _LXMF.LXMessage(dd, self.identity, content=text.encode("utf-8"))
                r.handle_outbound(m)
            else:
                dd = _RNS.Destination(rid, _RNS.Destination.OUT,
                                      _RNS.Destination.SINGLE, "rmeshv", "msg")
                _RNS.Resource(text.encode("utf-8"), dd)
            cid = dest_hex
            if cid not in self.messages:
                self.messages[cid] = []
            self.messages[cid].append({"from": "me", "text": text, "ts": time.time()})
            return True
        except:
            return False

    def get_peers(self):
        return list(self.discovered_peers.items())

    def get_announces(self):
        return list(self.announces)

    def get_interfaces(self):
        self._ri()
        return list(self.interfaces)

    def hs(self, h):
        return h[:16] if len(h) > 16 else h

    # ─── TCP Bridge fallback ────────────────────────────
    def bridge_connect(self, host, port):
        self.disconnect_bridge()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            s.settimeout(None)
            self.bridge = {"sock": s, "running": True}
            self._send_bridge({"type": "hello", "identity": self.identity_hash})
            t = threading.Thread(target=self._bridge_rx, daemon=True)
            t.start()
            # Try to read welcome
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

    def disconnect_bridge(self):
        if self.bridge:
            self.bridge["running"] = False
            try:
                self.bridge["sock"].close()
            except:
                pass
            self.bridge = None

    def _send_bridge(self, data):
        if not self.bridge:
            return
        try:
            self.bridge["sock"].sendall((json.dumps(data) + "\n").encode())
        except:
            self.disconnect_bridge()

    def _bridge_rx(self):
        buf = b""
        while self.bridge and self.bridge.get("running"):
            try:
                c = self.bridge["sock"].recv(4096)
                if not c:
                    break
                buf += c
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        msg = json.loads(line.decode())
                        self._handle_bridge_msg(msg)
                    except:
                        pass
            except:
                time.sleep(0.05)
        self.disconnect_bridge()

    def _handle_bridge_msg(self, msg):
        t = msg.get("type", "")
        if t == "message":
            f = msg.get("from", msg.get("from_hash", "?"))
            tx = msg.get("text", "")
            cid = f
            if cid not in self.messages:
                self.messages[cid] = []
            self.messages[cid].append({"from": cid[:16], "text": tx, "ts": msg.get("timestamp", time.time())})
        elif t == "peers":
            for p in msg.get("peers", []):
                h = p.get("hash", "")
                if h:
                    self.discovered_peers[h] = {"name": p.get("name", h[:12]), "last_seen": time.time()}


# ─── Base screen with dark styling ────────────────────
class DarkBox(Box):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.style.direction = COLUMN
        self.style.flex = 1
        self.style.background_color = C_BG


# ─── Messages ──────────────────────────────────────────
class MessagesScreen(DarkBox):
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

        self._poll()

    def _poll(self):
        self._check_incoming()
        threading.Timer(1.0, self._poll).start()

    def _check_incoming(self):
        if not self.node:
            return
        for cid, msgs in list(self.node.messages.items()):
            if cid == self.cdest or not self.cdest:
                for m in msgs:
                    if m.get("from") != "me":
                        self.add_bubble(f"[{m['from'][:12]}] {m['text']}", is_sent=False)
                self.node.messages[cid] = []
            else:
                # Has messages for another conversation
                pass

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
        if self.node:
            if self.node.rns_enabled and self.cdest:
                self.node.send_text(self.cdest, t)
            elif self.node.bridge:
                self.node._send_bridge({"type": "message", "to": self.cdest, "text": t, "timestamp": time.time()})


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
        if self.node.rns_enabled:
            ok = self.node.announce()
            self.st.text = "Announced via RNS!" if ok else "Failed"
        elif self.node.bridge:
            self.node._send_bridge({"type": "announce"})
            self.st.text = "Announced via bridge!"
        else:
            self.st.text = "Not connected"

    def ref(self, widget):
        if not self.node:
            self.pl.text = "No node"
            return
        peers = self.node.get_peers()
        if peers:
            self.pl.text = "\n".join(f"{h[:12]}... {p['name']}" for h, p in peers[:10])
        else:
            self.pl.text = "No peers discovered"
        self.st.text = f"{len(peers)} peer(s)"


# ─── Announces ─────────────────────────────────────────
class AnnouncesScreen(DarkBox):
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
        self._poll()

    def _poll(self):
        self.ref(None)
        threading.Timer(3.0, self._poll).start()

    def ref(self, widget):
        if not self.node:
            return
        ans = self.node.get_announces()
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
        ifaces = self.node.get_interfaces()
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
        h = self.node.identity_hash
        self.id_lbl.text = f"Identity:\n{h[:32]}..." if h else "Identity:\nN/A"
        if self.node.rns_enabled:
            self.st_lbl.text = f"RNS: ON | Peers: {len(self.node.get_peers())}"
        elif self.node.bridge:
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

        self.add(ml(f"ID: {self.node.identity_hash[:16]}...", size=10, color=C_TEXT_DIM, mb=4))
        self.add(ml("RMESHV v1.0.0", size=10, color=C_TEXT_DIM))
        self.add(ml("Reticulum " + (getattr(_RNS, "__version__", "?") if _RNS else "N/A"),
                     size=9, color=C_TEXT_DIM))

        # Load saved config
        c = self.node.config
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
        self.node.config["host"] = host
        self.node.config["port"] = port
        self.node.config["mode"] = "rns"
        self.node._sj("config.json", self.node.config)
        if self.node.bridge:
            self.node.disconnect_bridge()
        ok, msg = self.node.enable_rns(host, port)
        if ok:
            self.st.text = f"RNS enabled! via {host}:{port}"
            self.st.color = C_SUCCESS
            self.node.announce()
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
        self.node.config["host"] = host
        self.node.config["port"] = port
        self.node.config["mode"] = "bridge"
        self.node._sj("config.json", self.node.config)
        ok = self.node.bridge_connect(host, port)
        if ok:
            self.st.text = f"Bridge connected! {host}:{port}"
            self.st.color = C_SUCCESS
        else:
            self.st.text = "Bridge connection failed"
            self.st.color = C_WARN


# ─── Main App ──────────────────────────────────────────
class ReticulumMeshApp(App):
    def startup(self):
        self._running = True
        self.main_window = MainWindow(title="RMESHV")
        self.main_window.style.background_color = C_BG
        self.node = MeshNode()

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

    def ss(self, name):
        self.sc.clear()
        m = {
            "chat": lambda: MessagesScreen(self, self.node),
            "cnt": lambda: ContactsScreen(self.node),
            "ann": lambda: AnnouncesScreen(self.node),
            "iface": lambda: InterfacesScreen(self.node),
            "net": lambda: NetworkScreen(self.node),
            "set": lambda: SettingsScreen(self.node, self),
        }
        s = m.get(name, lambda: MessagesScreen(self, self.node))()
        self.sc.add(s)

    def exit(self):
        self._running = False
        if self.node:
            self.node.disconnect_bridge()
        return super().exit()


def main():
    return ReticulumMeshApp()
