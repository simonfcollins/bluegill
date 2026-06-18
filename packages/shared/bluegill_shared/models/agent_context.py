from dataclasses import dataclass

from ..utils.config import Workspace
from .message import Message
    
@dataclass(slots=True)
class AgentContext:
    workspace: Workspace
    messages: list[Message]
