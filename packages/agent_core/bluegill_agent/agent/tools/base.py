from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

class Tool(ABC):
    """
    A tool to be used by an agent upon request of the model.
    Features a run() function which defines the behavior of the tool.
    """
    
    name: str
    args: str
    description: str

    @abstractmethod
    async def run(self, input: dict[str, Any], working_dir: Path) -> str:
        """
        Executes the tool.
        
        Args:
            input - A mapping representing tool parameters.
            
        Returns:
            The result of executing the tool.
        """
        
        pass
