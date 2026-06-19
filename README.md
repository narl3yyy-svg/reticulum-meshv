# RMESHV — Reticulum Mesh Client

A modern desktop mesh networking client built on **Reticulum (RNS)** and **LXMF**, designed to work alongside **MeshChatX** on mobile devices.

## Features

### Messaging
- LXMF-based chat with delivery confirmation
- Conversation list with search
- File attachments show as bubbles in chat
- Message privacy filtering (all / trusted only / block unknown)
- Right-click to delete conversations

### Contacts
- Auto-discovery of peers via RNS announces
- Persistent contact storage with trust management
- Right-click to trust/untrust, copy hash, or delete
- Search contacts by name or hash

### Network
- Real-time peer discovery and tracking
- Active interface monitoring with RX/TX stats
- Known paths/hops display

### Interfaces
- This PC acts as a central node for phone connections
- AutoInterface + TCPServerInterface on port 4242 by default
- Shows your IP addresses so phones can connect
- Add TCP Client connections to phones
- Advanced config editor (opens as popup window)
- Live interface status (up/down counts, bytes in/out)

### Announces
- Automatic announce every 60 seconds
- Manual announce from sidebar or Announces tab
- See discovered peers with last-seen timestamps

### Files
- View received files in downloads folder
- Change download location
- Open folder directly from app

## Quick Start

### Install

```bash
git clone https://github.com/narl3yyy-svg/reticulum-meshv
cd reticulum-meshv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
python -m src.main
```

### Connect Your Phone

1. On the desktop app, go to **Interfaces** — it shows your PC's IP addresses and port 4242.
2. On your phone running MeshChatX, go to **Interfaces > Add > TCP Client**.
3. Enter your PC's IP and port **4242**.
4. Both devices should discover each other via announces within 60 seconds.

### Network Setup

The desktop app automatically configures RNS with:
- **AutoInterface** — discovers other RNS nodes on your local network
- **TCPServerInterface** on `0.0.0.0:4242` — allows phone connections

Make sure your firewall allows incoming TCP on port 4242.

## Architecture

```
src/
├── main.py                    # App entry point, backend init
├── config/
│   └── theme.py               # MeshChatX-matched dark theme
├── backend/
│   ├── rns_node.py            # RNS identity, interface status
│   ├── lxmf_messenger.py      # LXMF messaging, announces
│   ├── contact_manager.py     # Persistent contacts with trust
│   └── network_monitor.py     # Peer discovery, path tracking
└── ui/
    ├── main_window.py          # Collapsible sidebar navigation
    └── widgets/
        ├── messages_widget.py     # Chat with conversation list
        ├── contacts_widget.py     # Contact cards with trust/delete
        ├── announces_widget.py    # Discovered peers grid
        ├── network_widget.py      # Peers, interfaces, paths
        ├── interfaces_widget.py   # Node setup, status, config editor
        ├── file_manager_widget.py # Downloads viewer
        ├── telephony_widget.py    # LXST placeholder
        ├── settings_widget.py     # Identity, privacy, downloads
        └── common.py              # EmptyState, StatusDot
```

## Requirements

- Python >= 3.11
- RNS >= 1.3.5
- LXMF >= 1.0.1
- LXST >= 0.4.6
- PyQt6 >= 6.6.0

See `requirements.txt` for full list.

## Tech Stack

- **Python + PyQt6** — desktop GUI
- **Reticulum (RNS)** — mesh networking layer
- **LXMF** — messaging protocol over RNS
- **MeshChatX** — compatible mobile client (Android)

## License

Open source.
