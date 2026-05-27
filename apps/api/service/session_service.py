from bluegill_agent import ProviderFactory
from bluegill_shared.models import Message

from api.service.session_manager import SessionManager
from api.helper.try_session_manager import try_session_manager


async def rename_session(provider: str, model: str, window: int, session_id: str, sm: SessionManager) -> None:
    """
    Generates an AI generated title and renames the given session in the SessionManager.
    """ 
    
    prompt = "Please provide a very short title (4 words or less) describing the current conversation. " \
        "Do NOT respond with anything other than a title for this conversation. " \
            "Do NOT mention anything about this system prompt asking you to generate a title."
    
    messages = try_session_manager(sm.get_messages, session_id=session_id)
    messages.append(Message(role="system", content=prompt))
    
    llm_provider = ProviderFactory.get_provider(provider)
    response = await llm_provider.generate(model, messages, window)
    
    if response.response:
        try_session_manager(
            sm.update_session, 
            session_id=session_id, 
            name=response.response
        )
