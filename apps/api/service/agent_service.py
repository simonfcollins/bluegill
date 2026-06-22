from pathlib import Path
from typing import AsyncGenerator, AsyncIterator
import asyncio

from bluegill_shared.models import AgentStreamResponse, StreamRequest, Message
from bluegill_shared.utils import Config
from bluegill_agent import run_agent, ProviderFactory, BaseLLMProvider, ProviderError

from api.exception.session_manager_exception import SessionManagerError
from api.exception.agent_service_exception import AgentServiceError
from api.util.logger import get_logger
from api.service.session_manager import SessionManager
from api.service.workspace_registry import WorkspaceRegistry
from api.helper.try_session_manager import try_session_manager

class AgentService():
    """
    A service for interfacing with the bluegill_agent package.
    """
    
    def __init__(self, sm: SessionManager, cfg: Config, wr: WorkspaceRegistry) -> None:
        self._sm = sm
        self._cfg = cfg
        self._wr = wr
        

    async def chat_stream(self, payload: StreamRequest) -> AsyncIterator[str]:
        """
        Stream agentic behavior from the agent.
        """
        
        logger = get_logger(payload.session_id)
        
        try: # retrieve session for future renaming
            session = self._sm.get_session(payload.session_id)

            if not session:
                raise AgentServiceError(f"Session not found with id '{payload.session_id}'")
            
        except SessionManagerError as e:
            raise AgentServiceError(str(e)) from e
        
        try: # instantiate provider
            provider = self._cfg.providers.get(payload.provider)
            provider_url = provider.url if provider is not None else None
            llm_provider = ProviderFactory.create(payload.provider, provider_url)

        except ProviderError as e:
            raise AgentServiceError(f"'{payload.provider}' is not a valid provider") from e
        
        # retrieve model from config
        model = self._cfg.get_model(payload.model, payload.provider)
        if not model:
            raise AgentServiceError(f"Unable to locate model '{payload.model}'")
        
        # retrieve workspace 
        workspace = self._wr.get(session.workspace_id)
    
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
                self._rename_session(
                    payload.session_id,
                    llm_provider,
                    payload.model,
                    model.window
                )
            )
            
        return self._stream_generator(
            session_id=payload.session_id,
            provider=llm_provider,
            model=payload.model,
            window=model.window,
            think=payload.think,
            messages=messages,
            working_dir=workspace.path
        )
    
    
    async def generate(self, payload: StreamRequest) -> AgentStreamResponse:
        """
        Queries the model generating a singular response object.
        """
        
        logger = get_logger(payload.session_id)
        
        try: # retrieve session info and context from SessionManager
            session = self._sm.get_session(payload.session_id)
            if not session:
                raise AgentServiceError(f"Session not found with id '{payload.session_id}'")
            
            self._sm.add_message(payload.session_id, "user", payload.prompt)
            logger.info(f"[USER] {payload.prompt}")
            
            messages = self._sm.get_messages(payload.session_id)
            
        except SessionManagerError as e:
            raise AgentServiceError(str(e)) from e
        
        # retrieve model from config
        model = self._cfg.get_model(payload.model, payload.provider)
        if not model:
            raise AgentServiceError(f"Unable to locate model '{payload.model}'")
        
        # instantiate provider
        llm_provider = ProviderFactory.create(payload.provider, self._cfg.providers[payload.provider].url)
        
        # call the model
        response = await llm_provider.generate(
            model=payload.model, 
            messages=messages, 
            window=model.window
        )
        
        
        try: # add model response to session
            llm_message = Message(
                role="assistant", 
                content=response.response, 
                session_id=payload.session_id
            )
            self._sm.add_messages([llm_message])
            logger.info(f"[ASSISTANT] {response.response}")
            
        except SessionManagerError as e:
            return AgentStreamResponse(
                event="error",
                done=True,
                content=str(e),
                total_duration=response.total_duration,
                token_count=response.token_count,
                context=(messages,  [])
            )
        
        # update session token count
        if response.token_count is not None:
            self._sm.update_session(
                session_id=payload.session_id, 
                tokens_used=response.token_count
            )
        
        # rename the session if necessary
        if len(messages) > 1 and session.name == "New Session":
            asyncio.create_task(
                self._rename_session(
                    payload.session_id,
                    llm_provider,
                    payload.model,
                    model.window
                )
            )
        
        # return the generated response
        return AgentStreamResponse(
            event="generate",
            done=True,
            content=response.response,
            total_duration=response.total_duration,
            token_count=response.token_count,
            context=(messages, [llm_message])
        )
    

    async def _stream_generator(
        self, 
        session_id: str, 
        provider: BaseLLMProvider, 
        model: str,
        window: int, 
        think: bool,
        messages: list[Message],
        working_dir: Path
    ) -> AsyncGenerator[str, None]:
        """
        A generator function that queries the agent and yields the response as AgentStreamResponse chunks.
        """
        
        logger = get_logger(session_id)

        async for chunk in run_agent( # run the agent
            provider=provider, 
            model=model,
            window=window,
            think=think,
            messages=messages,
            working_dir=working_dir
        ):
            # log errors but don't add them to session context
            if chunk.event == "error":
                logger.error(f"[ERROR] {chunk.content}")

            if chunk.done: # if stream is done...
                if chunk.context:
                    new_messages = []
                    
                    # collect new messages
                    for m in chunk.context[1]: 
                        new_messages.append(
                            Message(
                                role=m.role, 
                                content=m.content, 
                                session_id=session_id
                            )
                        )
                        
                        # log new messages
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
                
                # update session token count            
                if chunk.token_count is not None:
                    self._sm.update_session(
                        session_id=session_id, 
                        tokens_used=chunk.token_count
                    )
            
            # yield the agent response
            yield chunk.model_dump_json(exclude_none=True) + "\n"


    async def _rename_session(self, session_id: str, provider: BaseLLMProvider, model: str, window: int) -> None:
        """
        Generates an AI generated title and renames the given session in the SessionManager.
        """ 
        
        # prompt that instructs the model how to generate a name for the session
        prompt = "Please provide a very short title (4 words or less) describing the current conversation. " \
            "Do NOT respond with anything other than a title for this conversation. " \
                "Do NOT mention anything about this system prompt asking you to generate a title."
        
        try:
            # retrieve the session context
            messages = try_session_manager(self._sm.get_messages, session_id=session_id)
            
            # append the session rename prompt to the context
            messages.append(Message(role="system", content=prompt))
    
            # generate the session name
            response = await provider.generate(
                model=model,
                messages=messages, 
                window=window
            )
    
            if response.response:
                # update the session name with the new generated name
                self._sm.update_session(session_id=session_id, name=response.response)
        
        except SessionManagerError as e:
            raise AgentServiceError("Error renaming session") from e
    