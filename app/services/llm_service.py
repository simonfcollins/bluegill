from typing import AsyncGenerator
from app.factory import ProviderFactory
from app.services.session_manager import session_manager
from app.services.logger import get_logger

class LLMService:
    @staticmethod
    async def generate(provider: str, model: str, new_messages: list[dict], session_id: str) -> str:
        logger = get_logger(session_id)
        llm_provider = ProviderFactory.get_provider(provider)
        
        # Store incoming messages
        for msg in new_messages:
            session_manager.add_message(
                session_id,
                msg["role"],
                msg["content"]
            )
            
            logger.info(f"[{msg['role'].upper()}] {msg['content']}")
            
        # Load full session context
        messages = session_manager.get_messages(session_id)
        
        # Call provider with full context
        response = await llm_provider.generate(messages, model)
        logger.info(f"[ASSISTANT] {response}")
        
        # Store response
        session_manager.add_message(session_id, "assistant", response)
        
        return response
