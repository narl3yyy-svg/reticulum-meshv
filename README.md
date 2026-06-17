# Reticulum Mesh (PyQt6)

A modern, feature-rich **PyQt6 desktop application** for mesh networking via **Reticulum Network Stack (RNS)**. 

**Key improvements**: Clean identity management (your mesh address is now stable and easy to share/copy), better UX for file transfers, input validation, and transfer history.

## Features

✅ **Easy Identity Sharing**
- Prominent display of your permanent identity hash
- One-click copy to clipboard (from status bar or Files tab)
- "Show Full Hash" button
- Clear instructions for sharing with peers

✅ **Advanced File Sharing**
- Unlimited file transfer size via chunked RNS transfers (64KB chunks) — *core transfer logic ready for real RNS.Resource implementation*
- Real-time progress tracking + history table
- SHA256 integrity verification (stub)
- Destination hash validation (must be valid 64-char hex)

✅ **Mesh Networking**
- Direct Reticulum integration (RNS ≥1.3.5)
- Persistent app identity separate from Reticulum daemon config
- LXMF / LXST ready (future voice & messaging)

✅ **Modern UI**
- Arch Linux-inspired dark theme
- Material Design components
- Responsive layouts with PyQt6

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

## Quick Start: Sharing Files on the Mesh

1. **Launch the app** (after starting `rnsd`)
2. Go to **📁 Files** tab
3. **Your Identity Hash** is prominently displayed at the top with **Copy Hash** button.
4. **Share your hash** with friends/peers (copy & send via any channel — Signal, email, etc.)
5. To **send a file**:
   - Click Browse and pick a file
   - Paste the **recipient's identity hash** into "Destination Hash"
   - Click **Send File over Mesh**
   - Watch live progress + history table

Your identity is **permanent** and stored in:
`~/.config/reticulum-meshv/identity.key`

Reticulum network config stays in the standard `~/.reticulum/`

## Identity Management (Fixed & Improved)

- **Stable ID**: Your hash never changes across restarts (loaded from disk)
- **Clean separation**: App identity is independent of Reticulum's internal identity
- **Easy copy**: Everywhere — status bar + big Copy button in Files view
- **Validation**: App checks that destination hashes are valid 64-hex-char strings

To backup/restore your identity, simply copy the `identity.key` file.

## Architecture

```
reticulum-meshv/
├── src/
│   ├── main.py                 # Entry point (config dirs)
│   ├── backend/
│   │   ├── rns_node.py        # Reticulum + persistent identity
│   │   └── file_transfer_manager.py
│   ├── ui/
│   │   ├── main_window.py     # Status bar + copy
│   │   └── widgets/
│   │       └── file_manager_widget.py  # Identity UI + validation
│   └── config/theme.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Future / Roadmap

- [x] Stable identity + easy sharing UI
- [ ] Real RNS file transfer using `RNS.Resource` (chunked, resumable, progress callbacks)
- [ ] Incoming file listener / receiver mode
- [ ] LXMF messaging integration
- [ ] LXST voice calls
- [ ] Contact list + saved destinations
- [ ] QR code for identity (easy mobile pairing with Sideband etc.)
- [ ] Settings panel for theme, interfaces

## Troubleshooting

**Identity not persisting?** Check `~/.config/reticulum-meshv/identity.key` exists and is readable.

**No network?** Make sure `rnsd` is running and interfaces are configured in `~/.reticulum/config`.

**Transfer stuck?** Currently in demo mode (simulated progress). Real mesh transfer implementation is the next step.

---

**Made for the mesh networking community** — now much easier to use!
