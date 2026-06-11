from typing import AsyncGenerator, AsyncIterator
import asyncio

from bluegill_shared.models import AgentStreamResponse, StreamRequest, Message
from bluegill_shared.utils import Config
from bluegill_agent import run_agent, ProviderFactory

from api.exception.session_manager_exception import SessionManagerError
from api.exception.agent_service_exception import AgentServiceError
from api.util.logger import get_logger
from api.service.session_manager import SessionManager
from api.service.session_service import rename_session

class AgentService():
    def __init__(self, sm: SessionManager, cfg: Config) -> None:
        self._sm = sm
        self._cfg = cfg
        
    async def chat_stream(self, payload: StreamRequest) -> AsyncIterator[str]:
        logger = get_logger(payload.session_id)
        
        try:
            session = self._sm.get_session(payload.session_id)
            
        except SessionManagerError as e:
            raise AgentServiceError(str(e)) from e
        
        if not session:
            raise AgentServiceError(f"Session not found with id '{payload.session_id}'")
    
        try:
            # add user prompt to the session
            self._sm.add_message(
                session_id=payload.session_id,
                role="user",
                content=payload.prompt
            )
            logger.info(f"[USER] {payload.prompt}")
            messages = self._sm.get_messages(payload.session_id)
        except SessionManagerError as e:
            raise AgentServiceError(str(e)) from e

        if len(messages) > 1 and session.name == "New Session":
            asyncio.create_task(
                rename_session(
                    payload.provider,
                    self._cfg.providers[payload.provider].url,
                    payload.model,
                    payload.window,
                    payload.session_id,
                    sm=self._sm
                )
            )
            
        return self._stream_generator(
            payload=payload,
            messages=messages
        )
    
    
    async def generate(self, payload: StreamRequest) -> AgentStreamResponse:
        
        logger = get_logger(payload.session_id)

        try: 
            self._sm.add_message(payload.session_id, "user", payload.prompt)
            logger.info(f"[USER] {payload.prompt}")
            
        except SessionManagerError as e:
            raise AgentServiceError(str(e)) from e
        
        try:
            messages = self._sm.get_messages(payload.session_id)

        except SessionManagerError as e:
            raise AgentServiceError(str(e)) from e
        
        llm_provider = ProviderFactory.create(payload.provider, self._cfg.providers[payload.provider].url)
        response = await llm_provider.generate(payload.model, messages, payload.window)
        
        llm_message = Message(
            role="assistant", 
            content=response.response, 
            session_id=payload.session_id
        )
        
        try:
            # add llm response to session
            self._sm.add_messages([llm_message])
            logger.info(f"[ASSISTANT] {response.response}")
        except SessionManagerError as e:
            return AgentStreamResponse(
                event="error",
                done=True,
                content=str(e),
                total_duration=response.total_duration,
                token_count=response.token_count,
                context=([m.model_dump() for m in messages],  [])
            )
        
        if response.token_count:
            self._sm.update_session(
                session_id=payload.session_id, 
                tokens_used=response.token_count
            )
        
        return AgentStreamResponse(
            event="generate",
            done=True,
            content=response.response,
            total_duration=response.total_duration,
            token_count=response.token_count,
            context=([m.model_dump() for m in messages], [llm_message.model_dump()])
        )
    

    async def _stream_generator(self, payload: StreamRequest, messages: list[Message]) -> AsyncGenerator[str, None]:
        
        logger = get_logger(payload.session_id)
        async for chunk in run_agent( # run the agent
            payload.provider, 
            self._cfg.providers[payload.provider].url,
            payload.model,
            messages,
            payload.window
        ):
            if chunk.event == "error":
                logger.error(f"[ERROR] {chunk.content}")

            if chunk.done: # if stream is done...
                if chunk.context:
                    new_messages = []
                    for m in chunk.context[1]: # collect new messages
                        new_messages.append(Message(
                            role=m.role, 
                            content=m.content, 
                            session_id=payload.session_id
                        ))
                        # log conversation
                        log = logger.warning if m.role == "system" else logger.info
                        log(f"[{m.role.capitalize()}] {m.content}")

                    if len(new_messages):
                        try:
                            # add new messages to session
                            self._sm.add_messages(new_messages)
                        except SessionManagerError as e:
                            logger.error(f"[ERROR] Failed to add new context to session")

                            yield AgentStreamResponse(
                                event="error",
                                content=f"Failed to add new context to session: {e}"
                            ).model_dump_json(exclude_none=True) + "\n"
                if chunk.token_count is not None:
                    self._sm.update_session(
                        session_id=payload.session_id, 
                        tokens_used=chunk.token_count
                    )
            
            # yield the agent response
            yield chunk.model_dump_json(exclude_none=True) + "\n"
