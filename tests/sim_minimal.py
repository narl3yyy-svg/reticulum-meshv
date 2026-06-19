"""Minimal test: single Reticulum with TCP server+client loopback, then check Transport."""
import os, sys, time, signal, tempfile
from pathlib import Path

# Patch signal BEFORE importing RNS
_orig_signal = signal.signal
signal.signal = lambda s, h: None

import RNS

d = Path(tempfile.mkdtemp(prefix="rns_sim_"))
for s in ["", "storage", "storage/cache", "storage/resources",
           "storage/identities", "storage/blackhole", "interfaces"]:
    (d / s).mkdir(parents=True, exist_ok=True)

port = 16161
config = f"""[reticulum]
enable_transport = True
share_instance = No
panic_on_interface_error = False

[logging]
loglevel = 2

[interfaces]
  [[Srv]]
    type = TCPServerInterface
    interface_enabled = Yes
    listen_ip = 127.0.0.1
    listen_port = {port}

  [[Cli]]
    type = TCPClientInterface
    interface_enabled = Yes
    target_host = 127.0.0.1
    target_port = {port}
"""
(d / "config").write_text(config)

r = RNS.Reticulum(configdir=str(d))

# Create two destinations to confirm they show up
ia = RNS.Identity()
da = RNS.Destination(ia, RNS.Destination.IN, RNS.Destination.SINGLE, "test", "a")
da.announce(b"hello from A")

ib = RNS.Identity()
db = RNS.Destination(ib, RNS.Destination.IN, RNS.Destination.SINGLE, "test", "b")
db.announce(b"hello from B")

time.sleep(5)

print(f"Transport has {len(RNS.Transport.destinations)} destinations:")
for dh in RNS.Transport.destinations:
    h = dh.hex() if hasattr(dh, 'hex') else str(dh)
    print(f"  {h[:48]}...")

# Check if loopback worked - should see both destinations
hashes = []
for dh in RNS.Transport.destinations:
    h = dh.hex() if hasattr(dh, 'hex') else str(dh)
    hashes.append(h)

a_seen = any(ia.hash.hex()[:12] in h for h in hashes)
b_seen = any(ib.hash.hex()[:12] in h for h in hashes)
print(f"\nDest A seen: {a_seen}")
print(f"Dest B seen: {b_seen}")
print(f"\nTest: {'PASS' if a_seen and b_seen else 'FAIL'}")
