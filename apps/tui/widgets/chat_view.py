from textual.containers import VerticalScroll

from widgets.chat_message import ChatMessage, MessageType


class ChatView(VerticalScroll):
    """
    Vertical container for displaying chat messages.
    """
    
    def __init__(self, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(id=id, classes=classes)
        
        
    def add_message(self, message_type: MessageType, content: str | None) -> ChatMessage:
        """
        Appends a new ChatMessage widget to self.
        """
        
        chat_message = ChatMessage(message_type, content or "")
        at_bottom = self.is_scrolled_bottom

        self.mount(chat_message)

        if at_bottom:
            self.scroll_end()

        return chat_message
        
        
    def clear(self) -> None:
        """
        Alias to self.remove_children()
        """
        
        self.remove_children()


    @property
    def is_scrolled_bottom(self) -> bool:
        return self.scroll_y >= self.max_scroll_y - 2
