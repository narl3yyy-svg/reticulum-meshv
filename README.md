# Reticulum Mesh (PyQt6)

A modern, feature-rich **PyQt6 desktop application** for mesh networking via **Reticulum Network Stack (RNS)**. Inspired by MeshChatX's architecture but built with native PyQt6 for desktop-first experience.

## Features

✅ **Advanced File Sharing**
- Unlimited file transfer size via chunked RNS transfers (64KB chunks)
- Real-time progress tracking
- SHA256 integrity verification
- Automatic retry on failure

✅ **Mesh Networking**
- Direct Reticulum integration (RNS ≥1.3.5)
- LXMF messaging support
- LXST for voice/calls
- Identity management with crypto signing

✅ **Modern UI**
- Arch Linux-inspired dark theme
- Material Design components
- Responsive layouts with PyQt6
- Async/await for non-blocking operations

✅ **Cross-Platform**
- Linux (primary: Arch, Debian, Fedora)
- macOS support
- Windows support

## Requirements

- **Python**: ≥3.11
- **Reticulum**: ≥1.3.5 installed and configured
- **Linux/macOS/Windows** with Python 3.11+

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/narl3yyy-svg/reticulum-meshv.git
cd reticulum-meshv
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 4. Initialize Reticulum (First Time Only)

If Reticulum isn't configured:

```bash
rnsd --initial-config
```

This creates `~/.reticulum/` with configuration files.

## Running the Application

### Option 1: Direct Python Execution

```bash
python -m src.main
```

### Option 2: Using Installed Script

```bash
pip install -e .
reticulum-meshv
```

### Option 3: From IDE

**VS Code/PyCharm**:
- Open project folder
- Select Python interpreter from venv
- Run `src/main.py`

## Quick Start Guide

### 1. First Launch

```bash
# Terminal 1: Ensure Reticulum daemon is running
rnsd

# Terminal 2: Launch application
cd ~/reticulum-meshv
source venv/bin/activate
python -m src.main
```

### 2. Send a File

1. Click **📁 Files** in sidebar
2. Click **Browse** and select a file
3. Enter recipient's **Destination Hash**
4. Click **Send File**
5. Monitor progress in real-time

### 3. Get Your Identity Hash

Your identity hash is displayed in the status bar on startup. Share it with peers to receive files.

## Architecture

```
reticulum-meshv/
├── src/
│   ├── main.py                 # Entry point
│   ├── config/
│   │   └── theme.py           # Arch dark theme + QSS styling
│   ├── backend/
│   │   ├── rns_node.py        # Reticulum integration
│   │   └── file_transfer_manager.py  # Chunked transfers
│   └── ui/
│       ├── main_window.py     # Main application window
│       └── widgets/
│           └── file_manager_widget.py  # File transfer UI
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Package configuration
└── README.md                  # This file
```

## Configuration

### Reticulum Config

Edit `~/.reticulum/config` to configure interfaces:

```ini
[reticulum]
timeouts_tcp = 120
timeouts_uncertainty = 20
defaults_timeout_messages = 15

[interfaces]
  [[LoopInterface]]
  interface_enabled = True
  
  [[TCPServerInterface]]
  interface_enabled = True
  listen_ip = 0.0.0.0
  listen_port = 4242
```

### Application Theme

Modify colors in `src/config/theme.py`:

```python
COLORS = {
    'primary': '#1F88E5',      # Arch Blue
    'background': '#1E1E1E',   # Deep gray
    # ... more colors
}
```

## Troubleshooting

### Issue: "Module 'src' not found"

**Solution**: Ensure you're in the project root and venv is activated:

```bash
cd ~/reticulum-meshv
source venv/bin/activate
python -m src.main
```

### Issue: "Reticulum not configured"

**Solution**: Initialize Reticulum:

```bash
rnsd --initial-config
# Then restart the application
```

### Issue: PyQt6 installation fails

**Solution**: Install system dependencies:

**Arch Linux**:
```bash
sudo pacman -S qt6-base
```

**Ubuntu/Debian**:
```bash
sudo apt install python3-pyqt6 libqt6gui6
```

**macOS**:
```bash
brew install qt6
```

### Issue: File transfer hangs

**Solution**: Check Reticulum connectivity:

```bash
rnstatus  # Shows network status
```

Ensure both peers are online and can reach each other.

## Development

### Adding New Features

1. **New Widget**:
   ```python
   # src/ui/widgets/my_feature_widget.py
   from PyQt6.QtWidgets import QWidget
   
   class MyFeatureWidget(QWidget):
       def __init__(self, backend):
           super().__init__()
           self.backend = backend
   ```

2. **Add to Main Window**:
   ```python
   # src/ui/main_window.py
   self.my_widget = MyFeatureWidget(backend)
   self.stack.addWidget(self.my_widget)
   ```

### Testing

Run tests (when added):

```bash
pytest tests/
```

### Code Style

Format with black:

```bash
pip install black
black src/
```

## Performance Tips

- **Large Files**: Use chunked transfers (automatic, 64KB chunks)
- **Network Latency**: Reticulum handles retries; be patient
- **Multiple Transfers**: Application queues transfers automatically
- **Memory**: Monitor with `psutil` for large file transfers

## Security

- **Identity**: RSA 2048-bit keys stored in `~/.reticulum/identities/`
- **Encryption**: All RNS messages encrypted end-to-end
- **File Hashing**: SHA256 verification on send/receive
- **No Telemetry**: All data stays local/on mesh

## Limitations

- ⚠️ **Python 3.11+** required (type hints)
- ⚠️ **Linux/macOS** primary support (Windows works but less tested)
- ⚠️ Desktop app only (no mobile yet)
- ⚠️ Requires active Reticulum daemon

## Future Roadmap

- [ ] Voice/video calls via LXST
- [ ] Message history with SQLite DB
- [ ] Offline message queuing
- [ ] Android/iOS via Kivy
- [ ] Web UI (FastAPI + Vue.js)
- [ ] PyInstaller packaging

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/awesome-feature`)
3. Commit changes (`git commit -am 'Add awesome feature'`)
4. Push to branch (`git push origin feature/awesome-feature`)
5. Open Pull Request

## License

GNU General Public License v3.0 - See `LICENSE` file

## Acknowledgments

- **MeshChatX** - Inspired by architecture and best practices
- **Reticulum** by Mark Qvist - Core networking stack
- **PyQt6** - Cross-platform GUI framework
- **Arch Linux** - Aesthetic inspiration

## Support

- 📖 **Documentation**: See this README
- 🐛 **Issues**: [GitHub Issues](https://github.com/narl3yyy-svg/reticulum-meshv/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/narl3yyy-svg/reticulum-meshv/discussions)

---

**Made with ❤️ for the mesh networking community**
