# app/agent/tools/base.py

from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(self, input: dict) -> str:
        pass