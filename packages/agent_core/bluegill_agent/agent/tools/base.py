from abc import ABC, abstractmethod
from typing import Any

class Tool(ABC):
    """
    A tool to be used by an agent upon request of the model.
    Features a run() function which defines the behavior of the tool.
    """
    
    name: str
    args: str
    description: str

    @abstractmethod
    async def run(self, input: dict[str, Any]) -> str:
        """
        Executes the tool.
        
        Args:
            input - A mapping representing tool parameters.
            
        Returns:
            The result of executing the tool.
        """
        
        pass
