"""TCP bridge server for mobile connections, relays to/from LXMF mesh."""
import json
import time
import socket
import threading
from pathlib import Path


class BridgeClientSession:
    def __init__(self, conn, addr, bridge):
        self.conn = conn
        self.addr = addr
        self.bridge = bridge
        self.identity = ""
        self.connected = True
        self.rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self.rx_thread.start()

    def _rx_loop(self):
        buf = b""
        while self.connected:
            try:
                chunk = self.conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line.decode("utf-8"))
                        self._handle(msg)
                    except json.JSONDecodeError:
                        pass
                    except Exception:
                        pass
            except:
                if self.connected:
                    time.sleep(0.05)
        self.connected = False
        self.bridge._on_disconnect(self)

    def send_msg(self, data):
        try:
            blob = json.dumps(data) + "\n"
            self.conn.sendall(blob.encode("utf-8"))
        except:
            self.connected = False

    def _handle(self, msg):
        t = msg.get("type", "")
        if t == "hello":
            self.identity = msg.get("identity", "")
            self.send_msg({"type": "welcome", "server_identity": self.bridge.server_identity})
            self.bridge._on_hello(self)
        elif t == "message":
            to = msg.get("to", "")
            text = msg.get("text", "")
            timestamp = msg.get("timestamp", time.time())
            self.bridge._on_message(self, to, text, timestamp)
        elif t == "announce":
            self.bridge._on_announce(self)
        elif t == "get_peers":
            self.bridge._on_get_peers(self)

    def close(self):
        self.connected = False
        try:
            self.conn.close()
        except:
            pass


class TCPBridgeServer:
    def __init__(self, lxmf_messenger=None, rns_node=None, host="0.0.0.0", port=4742):
        self.host = host
        self.port = port
        self.lxmf_messenger = lxmf_messenger
        self.rns_node = rns_node
        self.clients = {}
        self._lock = threading.Lock()
        self.server_identity = ""
        self._sock = None
        self._running = False
        self.message_callback = None

    def start(self):
        if self._running:
            return
        self._running = True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self.host, self.port))
            self._sock.listen(5)
            self._sock.settimeout(1)
        except Exception as e:
            print(f"[Bridge] Failed to start server: {e}")
            self._running = False
            return
        if self.rns_node:
            self.server_identity = self.rns_node.get_identity_hash()
        thread = threading.Thread(target=self._accept_loop, daemon=True)
        thread.start()
        print(f"[Bridge] TCP bridge listening on {self.host}:{self.port}")

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except:
                pass
        with self._lock:
            for c in list(self.clients.values()):
                c.close()
            self.clients.clear()

    def _accept_loop(self):
        while self._running:
            try:
                conn, addr = self._sock.accept()
                conn.settimeout(None)
                session = BridgeClientSession(conn, addr, self)
                with self._lock:
                    self.clients[session.identity] = session
            except socket.timeout:
                continue
            except:
                continue

    def _on_hello(self, session):
        old_key = None
        for k, v in list(self.clients.items()):
            if v is session:
                old_key = k
                break
        if old_key is not None and old_key != session.identity:
            with self._lock:
                if old_key in self.clients and self.clients[old_key] is session:
                    del self.clients[old_key]
                self.clients[session.identity] = session

    def _on_disconnect(self, session):
        with self._lock:
            key = None
            for k, v in list(self.clients.items()):
                if v is session:
                    key = k
                    break
            if key is not None and key in self.clients:
                del self.clients[key]
        if self.message_callback:
            self.message_callback("_bridge_", f"Phone disconnected: {session.identity[:16] if session.identity else session.addr[0]}", time.time())

    def _on_message(self, session, to, text, timestamp):
        sender = session.identity[:16] if session.identity else session.addr[0]
        if self.message_callback:
            self.message_callback(session.identity, f"{text}", timestamp)
        if to and self.lxmf_messenger:
            try:
                self.lxmf_messenger.send_message(to, text)
            except Exception as e:
                print(f"[Bridge] LXMF relay failed: {e}")

    def _on_announce(self, session):
        pass

    def _on_get_peers(self, session):
        with self._lock:
            connected = [
                {"hash": c.identity, "name": c.identity[:16]}
                for c in self.clients.values()
                if c.identity
            ]
        session.send_msg({"type": "peers", "peers": connected})

    def get_connected_clients(self):
        with self._lock:
            return list(self.clients.keys())

    def send_to_client(self, identity, msg_type, **kwargs):
        with self._lock:
            session = self.clients.get(identity)
        if session:
            data = {"type": msg_type, **kwargs}
            session.send_msg(data)
            return True
        return False

    def broadcast(self, msg_type, **kwargs):
        with self._lock:
            sessions = list(self.clients.values())
        data = {"type": msg_type, **kwargs}
        for s in sessions:
            s.send_msg(data)
