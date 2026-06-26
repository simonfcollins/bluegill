from textual.widgets import Button
import pyperclip

class CopyButton(Button):
    """
    Custom button that copies its stored text to the clipboard using pyperclip.
    """
    
    def __init__(self, text: str | None = "") -> None:
        super().__init__(
            label="Copy",
            classes="copy",
            flat=True
        )
        self.text = text


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Event handler for when this CopyButton is pressed.
        """
        
        if not self.text:
            return

        try:
            pyperclip.copy(self.text)
            self.notify("Copied to clipboard")
            
        except pyperclip.PyperclipException:
            self.notify("Clipboard unavailable", severity="warning")
