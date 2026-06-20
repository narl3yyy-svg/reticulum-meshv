[app]

# Application metadata
title = RMESHV
package.name = rmeshv
package.domain = com.narl3y

# Source code - include all .py files from src
source.dir = src
source.include_exts = py,png,jpg,kv,atlas

# Version
version = 1.0.0

# Requirements - only python3 and kivy from p4a. RNS, LXMF, configobj,
# pyserial are bundled as source in the src/ directory. RNS uses its
# internal crypto provider (no cryptography dependency needed).
requirements = python3,kivy

# Android build settings
orientation = portrait

# Fullscreen
fullscreen = 0

# Android API
android.api = 34

# Minimum SDK
minapi = 24

# NDK
android.ndk = 25b

# Build type
build_type = release

# Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_NETWORK_STATE,CHANGE_WIFI_MULTICAST_STATE,BLUETOOTH,BLUETOOTH_ADMIN,RECORD_AUDIO,VIBRATE,WAKE_LOCK,FOREGROUND_SERVICE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# Meta data
android.meta_data = org.kivy.android.launcher_fn=app:main

# Skip warnings
android.nopressure = 1

# logcat
logcat_filters = *:S RMESHV:V RNS:V LXMF:V Python:V

# p4a branch
p4a.branch = master

# NDK version
android.ndk_api = 24

# Skip license
android.accept_sdk_license = True

# Architectures - arm64 only to avoid 32-bit cross-compile issues
android.archs = arm64-v8a

#
# iOS
#
[buildozer]

log_level = 2
warn_on_root = 1
