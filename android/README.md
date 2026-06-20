# RMESHV Android

LXMF messaging client for Android, compatible with the RMESHV desktop app and MeshChatX.

## Building the APK

### Prerequisites

- Python 3.11 or 3.12 (NOT 3.13+ — buildozer/p4a doesn't support it yet)
- Java JDK 17
- Rust (for cryptography, if needed)
- Android SDK (auto-downloaded by buildozer)
- Android NDK (auto-downloaded by buildozer)

### Install build tools

```bash
# Use Python 3.11 or 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install buildozer cython

# Install Java JDK 17 (on Arch)
sudo pacman -S jdk17-openjdk

# Install Rust (for crypto packages)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env
```

### Build

```bash
cd android
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
export PATH=$JAVA_HOME/bin:~/.cargo/bin:$PATH
buildozer android debug
```

First build takes 30-40 minutes (downloads SDK/NDK, compiles Python for Android).

The APK will be at `android/bin/rmeshv-1.0.0-debug.apk`.

### Install on phone

```bash
adb install android/bin/rmeshv-1.0.0-debug.apk
```

Or copy the APK to your phone and install it manually.

## Features

- LXMF messaging (send/receive text and files)
- Peer discovery via RNS announces
- Message history persistence
- Settings tab with display name and server connection
- Dark theme matching desktop app
- Compatible with MeshChatX and RMESHV desktop

## Architecture

The app bundles RNS and LXMF as pure Python source code (no compiled dependencies).
RNS uses its internal crypto provider (pure Python) instead of the `cryptography` package,
which simplifies the Android build significantly.

```
android/
├── buildozer.spec      # Build configuration
└── src/
    ├── main.py         # Kivy app entry point
    ├── RNS/            # Reticulum Network Stack (bundled source)
    ├── LXMF/           # LXMF messaging protocol (bundled source)
    ├── configobj/      # Config parser (bundled source)
    └── serial/         # PySerial (bundled source)
```
