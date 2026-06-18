"""Basic BeeWare / Toga Android app skeleton."""

from toga import App, MainWindow, Box, Label, Button


class ReticulumMeshApp(App):
    def startup(self):
        self.main_window = MainWindow(title="Reticulum Mesh")

        box = Box()
        label = Label("Reticulum Mesh Mobile")
        button = Button("Hello from Toga", on_press=self.say_hello)

        box.add(label)
        box.add(button)

        self.main_window.content = box
        self.main_window.show()

    def say_hello(self, widget):
        print("Hello from the mobile app!")


def main():
    return ReticulumMeshApp()
