from bluegill_agent.providers.factory import ProviderFactory
from bluegill_agent.services.session_manager import session_manager
from bluegill_agent.services.logger import get_logger

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
        
        # Format messages to reduce token count
        messages_f = [{"role": m.role, "content": m.content} for m in messages]
        messages_f.reverse()
        print(messages_f)
    
        # Call provider with full context
        response = await llm_provider.generate(messages_f, model)
        logger.info(f"[ASSISTANT] {response}")
        
        # Store response
        session_manager.add_message(session_id, "assistant", response)
        
        return response
