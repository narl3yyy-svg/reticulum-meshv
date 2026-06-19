"""Run by simulation_test.py as a subprocess. Debug version."""
import os, sys, time, json, tempfile, signal, traceback
from pathlib import Path

import RNS

role = sys.argv[1]
port = int(sys.argv[2])
peer_port = int(sys.argv[3]) if sys.argv[3] != "0" else None
outfile = sys.argv[4]

d = tempfile.mkdtemp(prefix=f"rns_{role}_")
for s in ["", "storage", "storage/cache", "storage/resources",
           "storage/identities", "storage/blackhole", "interfaces"]:
    os.makedirs(os.path.join(d, s), exist_ok=True)

if role == "server":
    ifaces = f"""  [[{role}]]
    type = TCPServerInterface
    interface_enabled = Yes
    listen_ip = 127.0.0.1
    listen_port = {port}
"""
else:
    ifaces = f"""  [[{role}]]
    type = TCPClientInterface
    interface_enabled = Yes
    target_host = 127.0.0.1
    target_port = {peer_port}
"""

cfg = f"""[reticulum]
enable_transport = True
share_instance = No
panic_on_interface_error = False

[logging]
loglevel = 5

[interfaces]
{ifaces}
"""

Path(d, "config").write_text(cfg)

r = RNS.Reticulum(configdir=d, loglevel=7)

# Dump interfaces after init
print(f"[{role}] Interfaces:", flush=True)
for iface in list(getattr(RNS.Transport, "interfaces", [])):
    print(f"  {getattr(iface,'name','?')} OUT={getattr(iface,'OUT','?')} IN={getattr(iface,'IN','?')} online={getattr(iface,'online','?')} init={getattr(iface,'initiator','?')}", flush=True)

my_ident = RNS.Identity()
my_dest = RNS.Destination(my_ident, RNS.Destination.IN, RNS.Destination.SINGLE, "rmeshv-test", role)

data = {"role": role, "my_hash": my_ident.hash.hex(), "dest_hashes": [], "transport_hashes": []}

# Log all transport destinations BEFORE announce
for dh in list(RNS.Transport.destinations):
    h = dh.hex() if hasattr(dh, 'hex') else str(dh)[:48]
    data["transport_hashes"].append(h)

my_dest.announce(b"online")
data["announced"] = True

time.sleep(2)  # Wait for first exchange

# Log all transport destinations AFTER announce
for dh in list(RNS.Transport.destinations):
    h = dh.hex() if hasattr(dh, 'hex') else str(dh)[:48]
    if h not in data["dest_hashes"]:
        data["dest_hashes"].append(h)

# Now check more
for i in range(3):
    time.sleep(3)
    for dh in list(RNS.Transport.destinations):
        h = dh.hex() if hasattr(dh, 'hex') else str(dh)[:48]
        if h not in data["dest_hashes"]:
            data["dest_hashes"].append(h)
            print(f"[{role}] NEW: {h[:48]}", flush=True)

# Check path table too
data["path_table_keys"] = [k.hex() if hasattr(k, 'hex') else str(k) for k in list(getattr(RNS.Transport, "path_table", {}).keys())[:5]]
for k in getattr(RNS.Transport, "path_table", {}):
    data.setdefault("path_table_keys_all", []).append(k.hex() if hasattr(k, 'hex') else str(k))

Path(outfile).write_text(json.dumps(data))
