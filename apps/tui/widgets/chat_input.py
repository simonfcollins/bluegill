from textual.widgets import TextArea
from textual.message import Message
from textual import events


class ChatInput(TextArea):
    """
    Widget for entering text. 
    Triggers ChatInput.Submitted messages when text is submitted.
    """
    

    def __init__(self, **xargs) -> None:
        super().__init__(**xargs)
    

    async def on_key(self, event: events.Key) -> None:
        """
        Event handler for keystrokes.
        """
        
        if event.key == "enter":
            self.post_message(
                self.Submitted(
                    self,
                    self.text,
                )
            )
            self.clear()
            event.prevent_default()
            event.stop()
            return

        if event.key == "ctrl+enter":
            self.insert("\n")
            event.stop()
            return
        
        if event.key == "ctrl+a":
            self.select_all()
            event.stop()
            return


    class Submitted(Message):
        """
        Message indicating that text has been submitted.
        """
        
        def __init__(self, input: "ChatInput", value: str) -> None:
            super().__init__()
            self.input = input
            self.value = value
