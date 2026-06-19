"""
RMESHV Simulation Test: Two-node RNS-over-TCP connectivity.
"""
import os, sys, time, signal, tempfile, json, subprocess, threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
PASS = FAIL = 0
RESULTS = []

def check(name, ok, detail=""):
    global PASS, FAIL, RESULTS
    if ok:
        RESULTS.append(f"  PASS  {name}")
        PASS += 1
    else:
        RESULTS.append(f"  FAIL  {name}  {detail}")
        FAIL += 1

def main():
    global PASS, FAIL, RESULTS
    print("=" * 60)
    print("RMESHV Simulation Test")
    print("=" * 60)

    port_srv = 16441
    tmpdir = Path(tempfile.mkdtemp(prefix="rmeshv_sim_"))

    # 1. Start server process
    srv_file = tmpdir / "server.py"
    cli_file = tmpdir / "client.py"
    srv_out = tmpdir / "srv_out.json"
    cli_out = tmpdir / "cli_out.json"

    srv_script = f'''import os, sys, json, tempfile, time
from pathlib import Path
sys.path.insert(0, "{sys.path[0]}")
os.environ["RNS_DEBUG"] = "1"
import RNS
d = tempfile.mkdtemp(prefix="rns_srv_")
for s in ["","storage","storage/cache","storage/resources","storage/identities","storage/blackhole","interfaces"]:
    os.makedirs(os.path.join(d,s), exist_ok=True)
Path(d,"config").write_text("""[reticulum]
enable_transport = True
share_instance = No
panic_on_interface_error = False
[logging]
loglevel = 3
[interfaces]
  [[Srv]]
    type = TCPServerInterface
    interface_enabled = Yes
    listen_ip = 127.0.0.1
    listen_port = {port_srv}
""")
r = RNS.Reticulum(configdir=d)
ident = RNS.Identity()
dest = RNS.Destination(ident, RNS.Destination.IN, RNS.Destination.SINGLE, "rmeshv", "server")
dest.announce(b"server online")
time.sleep(5)
dest.announce(b"server re-announce")
time.sleep(5)
paths = []
for ph in RNS.Transport.path_table:
    h = ph.hex() if hasattr(ph,"hex") else str(ph)
    paths.append(h)
json.dump({{"hash": ident.hash.hex(), "paths": paths}}, open("{srv_out}","w"))
'''

    cli_script = f'''import os, sys, json, tempfile, time
from pathlib import Path
sys.path.insert(0, "{sys.path[0]}")
os.environ["RNS_DEBUG"] = "1"
import RNS
d = tempfile.mkdtemp(prefix="rns_cli_")
for s in ["","storage","storage/cache","storage/resources","storage/identities","storage/blackhole","interfaces"]:
    os.makedirs(os.path.join(d,s), exist_ok=True)
Path(d,"config").write_text("""[reticulum]
enable_transport = True
share_instance = No
panic_on_interface_error = False
[logging]
loglevel = 3
[interfaces]
  [[Cli]]
    type = TCPClientInterface
    interface_enabled = Yes
    target_host = 127.0.0.1
    target_port = {port_srv}
""")
r = RNS.Reticulum(configdir=d)
ident = RNS.Identity()
dest = RNS.Destination(ident, RNS.Destination.IN, RNS.Destination.SINGLE, "rmeshv", "client")
dest.announce(b"client online")
time.sleep(5)
dest.announce(b"client re-announce")
paths = []
for ph in RNS.Transport.path_table:
    h = ph.hex() if hasattr(ph,"hex") else str(ph)
    paths.append(h)
json.dump({{"hash": ident.hash.hex(), "paths": paths}}, open("{cli_out}","w"))
'''

    srv_file.write_text(srv_script)
    cli_file.write_text(cli_script)

    print(f"[1] Starting server on port {port_srv}...")
    srv_proc = subprocess.Popen([sys.executable, "-u", str(srv_file)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    print("[2] Starting client...")
    cli_proc = subprocess.Popen([sys.executable, "-u", str(cli_file)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[3] Waiting for test completion (16s)...")
    time.sleep(16)

    print("[4] Terminating...")
    for p in [srv_proc, cli_proc]:
        p.terminate()
        try: p.wait(timeout=5)
        except: p.kill()

    # Read results
    try:
        srv_data = json.loads(srv_out.read_text())
        cli_data = json.loads(cli_out.read_text())
    except Exception as e:
        print(f"  Error reading results: {e}")
        srv_data = {}
        cli_data = {}

    srv_hash = srv_data.get("hash", "")
    cli_hash = cli_data.get("hash", "")
    srv_paths = srv_data.get("paths", [])
    cli_paths = cli_data.get("paths", [])

    print()
    print("[5] Results:")
    check("Server identity created", bool(srv_hash))
    check("Client identity created", bool(cli_hash))
    check("Hashes differ", srv_hash != cli_hash)
    check("Server has >= 1 path entry (remote destination)",
          len(srv_paths) >= 1, f"got {srv_paths}")
    check("Client has >= 1 path entry (remote destination)",
          len(cli_paths) >= 1, f"got {cli_paths}")
    if len(srv_paths) >= 1 and len(cli_paths) >= 1:
        check("Path entries are different (client != server)",
              srv_paths[0] != cli_paths[0] if len(srv_paths) > 0 and len(cli_paths) > 0 else True)

    print(f"  Server hash: {srv_hash[:16]}...  paths={srv_paths}")
    print(f"  Client hash: {cli_hash[:16]}...  paths={cli_paths}")

    print()
    print("=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL}")
    for r in RESULTS:
        print(r)
    print("=" * 60)

    import shutil
    shutil.rmtree(str(tmpdir), ignore_errors=True)
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
