from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual import on
from textual.binding import Binding

class Confirm(ModalScreen[bool]):

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, dialog: str) -> None:
        super().__init__()
        self.dialog = dialog
        self._yes_button = Button("Yes", id="yes", variant="error", classes="yes-button")
        self._no_button = Button("Cancel", id="no")

    
    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.dialog)
            with Horizontal():
                yield self._yes_button
                yield self._no_button


    def on_mount(self):
        self._no_button.focus()


    @on(Button.Pressed)
    def _on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Event handler for when a list item is selected.
        Yields the name of the list item.
        """
        
        self.dismiss(event.button.variant == "error")


    def action_cancel(self) -> None:
        """
        Textual action to dismiss this Confirm widget without doing anything.
        Bound to the 'escape' key.
        """
        
        self.dismiss(False)
