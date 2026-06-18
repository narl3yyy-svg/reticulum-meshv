"""Reticulum Mesh - Mobile App (BeeWare / Toga)

Typical mobile layout with bottom navigation.
"""

import sys
from pathlib import Path

# Allow importing from the main repo's backend during development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from toga import (
    App, MainWindow, Box, Label, Button, ScrollContainer,
    TextInput
)
from toga.style import Pack

from toga.constants import COLUMN, ROW

from src.backend import ReticulumNode


class MessagesScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, padding=10))

        self.add(Label("Messages", style=Pack(font_size=20, padding_bottom=10)))

        self.messages = ScrollContainer(style=Pack(flex=1))
        self.messages.content = Label("No messages yet.\n\nThis will show your Reticulum conversations.")
        self.add(self.messages)

        input_box = Box(style=Pack(direction=ROW, padding_top=10))
        self.input = TextInput(placeholder="Type a message...", style=Pack(flex=1))
        send_btn = Button("Send", on_press=self.send_message)
        input_box.add(self.input)
        input_box.add(send_btn)
        self.add(input_box)

    def send_message(self, widget):
        text = self.input.value.strip()
        if text:
            print(f"[Messages] Sending: {text}")
            self.input.value = ""


class FilesScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, padding=10))
        self.add(Label("Files", style=Pack(font_size=20, padding_bottom=10)))
        self.add(Label("File transfer screen will go here.\n\nYou will be able to send/receive files over Reticulum."))


class ContactsScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, padding=10))
        self.add(Label("Contacts", style=Pack(font_size=20, padding_bottom=10)))
        self.add(Label("Discovered peers and saved contacts will appear here."))


class SettingsScreen(Box):
    def __init__(self):
        super().__init__(style=Pack(direction=COLUMN, padding=10))
        self.add(Label("Settings", style=Pack(font_size=20, padding_bottom=10)))
        self.add(Label("App settings and Reticulum configuration."))


class ReticulumMeshApp(App):
    def startup(self):
        self.main_window = MainWindow(title="Reticulum Mesh")

        # Try to initialize Reticulum node (will be expanded later)
        try:
            self.rns_node = ReticulumNode(
                rns_config_dir=str(Path.home() / ".reticulum"),
                app_config_dir=str(Path.home() / ".config" / "reticulum-mesh-mobile")
            )
            print("ReticulumNode initialized successfully on mobile.")
        except Exception as e:
            print(f"Failed to init ReticulumNode: {e}")
            self.rns_node = None

        # Main content container
        self.content_box = Box(style=Pack(direction=COLUMN, flex=1))

        # Bottom navigation
        nav_bar = Box(style=Pack(direction=ROW, padding=8, background_color="#1f1f1f"))

        for name in ["Messages", "Files", "Contacts", "Settings"]:
            btn = Button(name, on_press=lambda w, n=name.lower(): self.show_screen(n))
            btn.style.flex = 1
            nav_bar.add(btn)

        self.screen_container = Box(style=Pack(direction=COLUMN, flex=1))

        self.content_box.add(self.screen_container)
        self.content_box.add(nav_bar)

        self.main_window.content = self.content_box
        self.main_window.show()

        self.show_screen("messages")

    def show_screen(self, screen_name):
        self.screen_container.clear()

        if screen_name == "messages":
            self.screen_container.add(MessagesScreen())
        elif screen_name == "files":
            self.screen_container.add(FilesScreen())
        elif screen_name == "contacts":
            self.screen_container.add(ContactsScreen())
        elif screen_name == "settings":
            self.screen_container.add(SettingsScreen())


def main():
    return ReticulumMeshApp()
