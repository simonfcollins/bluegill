import pyperclip
from rich.syntax import Syntax

from textual.widgets import Static
from textual.message import Message


class CodeBlock(Static):
    """
    A custom textual.Static widget for rendering blocks of code 
    using rich.syntax. 
    """
    
    def __init__(self, text: str, lang: str) -> None:
        super().__init__(Syntax(text, lang, theme="native", padding=1))
        self.text = text
        self.lang = lang
        self.tooltip = "Click to copy"
        
        
    def on_click(self) -> None:
        """
        On click action that copies this widget's text to the clipboard.
        """
        
        if not self.text:
            return

        try:
            pyperclip.copy(self.text)
            self.notify("Copied to clipboard")
            
        except pyperclip.PyperclipException:
            self.notify("Clipboard unavailable", severity="warning")
            self.post_message(self.Clicked(self))


    class Clicked(Message):
        def __init__(self, sender: "CodeBlock") -> None:
            self.sender = sender
            super().__init__()
         