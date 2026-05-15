from httpx import HTTPStatusError
import json
import re
from typing import Any, AsyncGenerator

from bluegill_shared.models import Message, AgentStreamResponse, Role

from bluegill_agent.providers.factory import ProviderFactory
from bluegill_agent.agent.tool_registry import TOOLS
from bluegill_agent.agent.system_prompt import SYSTEM_PROMPT
from bluegill_agent.agent.constants import MIN_WINDOW
from bluegill_agent.exceptions.tool_exception import ToolExecutionError
from bluegill_agent.exceptions.agent_exception import JSONParseError
from bluegill_agent.exceptions.safe_path_exception import SafePathError
from bluegill_agent.exceptions.tool_exception import ToolNotFoundError
from bluegill_agent.exceptions.provider_exception import InvalidProviderError, ProviderError


MAX_ITERATIONS = 20

    
def _parse_json(text: str) -> Any:
    """
    Uses the built-in JSON library to strip and parse JSON objects.
    """
    
    try:
        cleaned = re.sub(r"```json|```", "", text).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise JSONParseError(f"Error parsing JSON: {e}")
    
    
def _parse_tool_call(text: str) -> AgentStreamResponse:
    """
    Parses a tool call from the agent into a AgentStreamResponse object.
    Expects tool calls in the following format: 
    '[TOOL]{"tool": "tool_name", "input": {"param1": "arg1", "param2", "arg2", ...}}[/TOOL]'
    """
    
    # extract content between [TOOL] ... [/TOOL]
    match = re.search(r"\[TOOL\](.*?)\[/TOOL\]", text, re.DOTALL)

    if not match:
        raise JSONParseError(f"Error parsing tool call: {text}")

    tool_call = match.group(1).strip()

    data = _parse_json(tool_call)

    if "tool" in data and "input" in data:
        return AgentStreamResponse(
            event="tool_call",
            content=tool_call,
            tool=data["tool"],
            input=data["input"]
        )

    raise JSONParseError(f"Error parsing tool call: {text}")


async def run_agent(
    provider: str, 
    model: str, 
    messages: list[Message], 
    window: int
) -> AsyncGenerator[AgentStreamResponse, None]:
    """
    The entrypoint for the Bluegill agent. Streams the agent's response and tool 
    executions in response to the given message chain.
    """
    
    def create_message(role: Role, content: str) -> None:
        """
        Adds a message to the growing agent context.
        """
        
        message = Message(role=role, content=content)
        full_context.append(message)
        new_context.append(message) 
    
    
    # input validation =========================================================
    
    if window < MIN_WINDOW:
        yield AgentStreamResponse(
            event="error",
            done=True,
            content=f"Agent context window must be >= {MIN_WINDOW}",
            total_duration=0,
            token_count=0,
            context=([m.model_dump() for m in messages], [])
        )
        return
        
    if not messages:
        yield AgentStreamResponse(
            event="error",
            done=True,
            content="No messages received",
            total_duration=0,
            token_count=0,
            context=([m.model_dump() for m in messages], [])
        )
        return
    
    try:
        llm_provider = ProviderFactory.get_provider(provider)
    except InvalidProviderError as e:
        yield AgentStreamResponse(
            event="error",
            done=True,
            content=str(e),
            total_duration=0,
            token_count=0,
            context=([m.model_dump() for m in messages], [])
        )
        return
    
    try:
        if not await llm_provider.model_exists(model):
            yield AgentStreamResponse(
                event="error",
                done=True,
                content=f"Model '{model}' not found",
                total_duration=0,
                token_count=0,
                context=([m.model_dump() for m in messages], [])
            )
            return
    except ProviderError as e:
        yield AgentStreamResponse(
            event="error",
            done=True,
            content=str(e),
            total_duration=0,
            token_count=0,
            context=([m.model_dump() for m in messages], [])
        )
        return       
        
    full_context = messages.copy()
    new_context: list[Message] = []
    total_duration = 0
    token_count = 0
    i = 0

    for i in range(MAX_ITERATIONS):
        buffer_str = ""
        tool_call = False
        check_tool_call = True
        stream_complete = False
        
        try:
            async for chunk in llm_provider.stream(
                model=model,
                messages=full_context,
                system_prompt=SYSTEM_PROMPT, 
                window=window
            ):
                if chunk.done:
                    total_duration += chunk.total_duration
                    token_count += chunk.token_count
                    stream_complete = True
                    break
                
                buffer_str += chunk.response

                if check_tool_call:
                    if "[TOOL]" in buffer_str:  # this message is a tool_call...
                        check_tool_call = False # so don't check anymore
                        tool_call = True
                    elif len(buffer_str) > 20:  # we can assume this isn't a tool call...
                        check_tool_call = False # so don't check anymore...
                        yield AgentStreamResponse(    # and yield the entire response up to this point
                            event="generate",
                            content=buffer_str, 
                        )
                else:
                    if not tool_call:
                        yield AgentStreamResponse( # yield just the current chunk moving forward
                            event="generate",
                            content=chunk.response,
                        )
                    # else: wait for full tool_call to be generated
                    
        except ProviderError as e:
            create_message("system", str(e))
            
            yield AgentStreamResponse(
                event="error",
                done=True,
                content=str(e),
                total_duration=total_duration,
                token_count=token_count,
                context=(
                    [m.model_dump() for m in messages],
                    [m.model_dump() for m in new_context]
                )
            )
            return
        
        if not stream_complete:
            create_message("system", "Provider stream ended unexpectedly")
            
            yield AgentStreamResponse(
                event="error",
                done=True,
                content="Provider stream ended unexpectedly",
                total_duration=total_duration,
                token_count=token_count,
                context=(
                    [m.model_dump() for m in messages],
                    [m.model_dump() for m in new_context]
                )
            )
            return
                
        if tool_call: # enter tool call chain
            try:
                response = _parse_tool_call(buffer_str) # parse the tool call
                
                create_message("assistant", response.content)
                
                yield response # yield the assistant's tool call
                
                tool = TOOLS.get(response.tool)
    
                if not tool:
                    raise ToolNotFoundError(f"'{response.tool}' tool does not exist")
            
                tool_result = await tool.run(response.input) # run the tool
                create_message("tool", tool_result)

                yield AgentStreamResponse( # yield the result of the tool call
                    event="tool_result",
                    content=tool_result,
                    tool=response.tool,
                    input=response.input
                )
                continue
            
            except ToolNotFoundError:
                create_message("system", f"{response.tool} does not exist")
                
                yield AgentStreamResponse(
                    event="error",
                    content=f"'{response.tool}' tool does not exist"
                )
                continue
            
            except ToolExecutionError as e:
                create_message("system", f"An error was encountered when trying to run tool '{response.tool}': {e}")
           
                yield AgentStreamResponse(
                    event="error",
                    content=f"An error was encountered when trying to run tool '{response.tool}': {e}"
                )
                continue
            
            except SafePathError as e:
                create_message("system", f"Error running tool '{response.tool}': {e}")
                
                yield AgentStreamResponse(
                    event="error",
                    content=f"Error running tool '{response.tool}': {e}"
                )
                continue
            
            except JSONParseError:
                create_message(
                    "system", 
                    "Error parsing JSON. Your previous response was malformed and could not be parsed. Please try again"
                )
                
                yield AgentStreamResponse(
                    event="error",
                    content="Error parsing JSON. Your previous response was malformed and could not be parsed. Please try again"
                )
                continue

            except Exception:
                create_message("system", "An unexpected error occurred")
                
                yield AgentStreamResponse(
                    event="error",
                    content="An unexpected error occurred"
                )
                continue
            
        else: # final response. Already yielded response so just add to session and return.
            create_message("assistant", buffer_str)
            yield AgentStreamResponse(
                done=True,
                total_duration=total_duration,
                token_count=token_count,
                context=(
                    [m.model_dump() for m in messages],
                    [m.model_dump() for m in new_context]
                )
            )
            return
    
    if i == MAX_ITERATIONS - 1: # max iterations reached
        yield AgentStreamResponse(
            event="error",
            done=True,
            content="Max steps reached",
            total_duration=total_duration,
            token_count=token_count,
            context=(
                [m.model_dump() for m in messages],
                [m.model_dump() for m in new_context]
            )
        ) 
        return
           