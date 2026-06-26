import json
from typing import Literal
from textual.widgets import Label
from textual.containers import Vertical

from widgets.markdown_view import MarkdownView

# an amalgamation of AgentEvent and Role literal 
# types from the bluegill_shared package
MessageType = Literal[
    "user",
    "assistant",
    "tool",
    "system",
    "generate",
    "error",
    "tool_call",
    "tool_result",
    "thinking"
]


class ChatMessage(Vertical):
    """
    Widget for displaying a variety of agent and user messages.
    Renders content differently based on the message type.
    """
    
    def __init__(
        self, 
        message_type: MessageType,
        content: str | None = ""
    ) -> None:
        super().__init__(classes="wrapper")
        self.message_type = message_type
        self.content = content or ""
        self.widget = None

        match message_type:
            case "user":
                self.widget = Label(self.content, classes="msg user", markup=False)
                self.add_class("user")
            
            case "generate":
                self.widget = Label(self.content, classes="msg agent")
                self.add_class("agent")
                
            case "tool_call" | "assistant":
                try: 
                    # try to parse tool call
                    tool_call = dict(json.loads(self.content))
                    tool_name = tool_call["tool"]
                    tool_args = dict(tool_call.get("input", {}))
                    tool_path = tool_args.get("path", "")
                    command = tool_args.get("command", "")
                    
                    self.widget = Label(
                        f"[green]\[{tool_name}][/green] [dim]{tool_path or command}[/dim]\n", 
                        classes="msg tool-call"
                    )
                    
                except Exception:
                    self.widget = MarkdownView(self.content, classes="msg agent")
                    
                finally:  
                    self.add_class("agent")
                
            case "error" | "system":
                self.widget = Label(f"[red]{self.content}[/red]\n", classes="msg system")
                self.add_class("agent")

            case "tool_result" | "tool":
                self.widget = Label(self.content, classes="msg tool")
                self.add_class("agent")
                
            case "thinking":
                self.widget = Label(self.content, classes="msg agent think")
                self.add_class("agent")
        
        self._add_child(self.widget)
                
                
    def update(self, content: str) -> None:
        """
        Update the widget's content area with a string.
        """
        
        if content == self.content:
            return
        
        self.content = content
        
        if self.widget is None:
            return
        
        self.widget.update(self.content)
        
    
    def render_final(self) -> None:
        """
        Call to re-render the widget once it's content is complete.
        """
        
        # if message_type is generate then self.widget is a textual.widgets.Label
        # re-render the Label as a MarkdownView
        if self.message_type == "generate" and self.widget:
            self.remove_children()
            self.widget = MarkdownView(str(self.content), classes=" ".join(self.widget.classes))
            self.mount(self.widget)
