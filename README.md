# Reticulum Mesh (PyQt6)

A modern, feature-rich **PyQt6 desktop application** (with mobile companion) for mesh networking via **Reticulum Network Stack (RNS)**.

**v0.3.0 — Polished UI & Desktop–Mobile Bridge**

## Features

✅ **LXMF Messaging**
- Proper LXMF-based messaging with delivery receipts
- Conversation management with history
- LXMF propagation node support
- Full message persistence

✅ **Multi-Identity Management**
- Create, switch, and manage multiple Reticulum identities
- Import/export identity key files
- Per-identity configuration

✅ **Contact Management**
- Persistent contact storage with names and notes
- Auto-discovery of peers via network announces
- Search, rename, and delete contacts
- Quick-start chat from contact list

✅ **Network Visualizer**
- Real-time peer discovery and tracking
- Active interface monitoring (RX/TX stats)
- Known paths/hops display
- Auto-refreshing topology view

✅ **LXST Telephony (Voice Calls)**
- Initiate and receive voice calls over the mesh
- Call state management (ringing, active, ended)
- Call history tracking
- LXST identity and destination registration

✅ **Easy Identity Sharing**
- Prominent display of permanent identity hash
- One-click copy to clipboard
- Clear instructions for sharing with peers

✅ **Advanced File Sharing**
- Unlimited file transfer size via chunked RNS transfers
- Real-time progress tracking + history table
- SHA256 integrity verification
- Destination hash validation

✅ **Mesh Networking**
- Direct Reticulum integration (RNS ≥1.3.5)
- LXMF and LXST ready
- Persistent app identity separate from Reticulum daemon config

✅ **Mobile Companion App**
- Android app via BeeWare/Briefcase
- LXMF messaging on mobile
- Contact management
- Network status monitoring

✅ **Modern UI**
- Arch Linux-inspired dark theme
- Material Design components
- Responsive layouts with PyQt6
- Empty-state placeholders for all widgets
- Status-dot indicators (online/offline/away)
- Thread-safe QTimer-based auto-refresh

## Requirements

- **Python**: ≥3.11
- **Reticulum**: ≥1.3.5 installed and configured (`rnsd`)
- **PyQt6** and other deps in requirements.txt

## Installation & Running

```bash
git clone https://github.com/narl3yyy-svg/reticulum-meshv.git
cd reticulum-meshv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# First time Reticulum setup (if needed)
rnsd --initial-config

# Run daemon in one terminal
rnsd

# Run app in another
python -m src.main
```

## Mobile App (Android)

```bash
cd mobile/reticulum_mesh
briefcase run android
```

## Architecture

```
reticulum-meshv/
├── src/
│   ├── main.py                    # Entry point
│   ├── backend/
│   │   ├── rns_node.py           # Reticulum + persistent identity
│   │   ├── file_transfer_manager.py
│   │   ├── lxmf_messenger.py     # LXMF messaging
│   │   ├── identity_manager.py   # Multi-identity lifecycle
│   │   ├── contact_manager.py    # Persistent contacts
│   │   ├── network_monitor.py    # Topology tracker
│   │   └── telephony_manager.py  # LXST voice calls
│   ├── ui/
│   │   ├── main_window.py        # 9-tab sidebar navigation + status bar
│   │   └── widgets/
│   │       ├── common.py          # Shared EmptyState + StatusDot components
│   │       ├── messages_widget.py # Two-pane chat with bubbles + unread badges
│   │       ├── file_manager_widget.py
│   │       ├── contacts_widget.py
│   │       ├── identities_widget.py
│   │       ├── network_widget.py  # Peer/interface/path tables
│   │       ├── telephony_widget.py
│   │       ├── interfaces_widget.py
│   │       └── settings_widget.py
│   └── config/theme.py
├── mobile/reticulum_mesh/         # BeeWare Android app
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Future / Roadmap

- [x] Stable identity + easy sharing UI
- [x] LXMF messaging with delivery receipts
- [x] Multi-identity management
- [x] Persistent contact management
- [x] Network visualizer
- [x] LXST telephony (voice calls)
- [ ] Real RNS file transfer using `RNS.Resource` (chunked, resumable)
- [ ] Incoming file receiver mode
- [ ] QR code for identity (easy mobile pairing)
- [x] Settings panel for interfaces, downloads, identity
- [ ] Settings panel for theme

## Troubleshooting

**Identity not persisting?** Check `~/.config/reticulum-meshv/identity.key` exists.

**No network?** Make sure `rnsd` is running and interfaces configured.

**LXMF not working?** Ensure LXMF library is installed (`pip install LXMF`).

---

**Made for the mesh networking community**
