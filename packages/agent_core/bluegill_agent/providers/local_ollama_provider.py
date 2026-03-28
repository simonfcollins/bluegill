import httpx
import json
from .base import BaseLLMProvider

def format_messages(messages: list[dict]) -> str:
    prompt = ""
        
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            prompt += f"[SYSTEM]\n{content}\n\n"
        elif role == "user":
            prompt += f"[USER]\n{content}\n\n"
        elif role == "assistant":
            prompt += f"[ASSISTANT]\n{content}\n\n"
        elif role == "tool":
            prompt += f"[TOOL]\n{content}\n\n"
                
    prompt += "ASSISTANT\n"
    return prompt

class LocalOllamaProvider(BaseLLMProvider):
  
    async def generate(self, messages: list[dict], model: str) -> str:
        async with httpx.AsyncClient() as client:
            prompt = format_messages(messages) # TODO : decide whether or not to use this
            
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": model,
                    "prompt": json.dumps(messages),
                    "stream": False,
                    "think": False
                },
                timeout=120,
            )
            data = response.json()
            return data.get("response", "")
        