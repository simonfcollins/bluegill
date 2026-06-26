import json
import re
from typing import Any, AsyncGenerator
from pathlib import Path

from bluegill_shared.models import Message, AgentStreamResponse, Role

from bluegill_agent.providers.base import BaseLLMProvider
from bluegill_agent.agent.tool_registry import TOOLS
from bluegill_agent.agent.system_prompt import SYSTEM_PROMPT
from bluegill_agent.agent.constants import MIN_WINDOW
from bluegill_agent.exceptions.tool_exception import ToolExecutionError
from bluegill_agent.exceptions.agent_exception import JSONParseError
from bluegill_agent.exceptions.safe_path_exception import SafePathError
from bluegill_agent.exceptions.tool_exception import ToolNotFoundError
from bluegill_agent.exceptions.provider_exception import ProviderError


MAX_ITERATIONS = 25

    
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
    provider: BaseLLMProvider, 
    model: str, 
    messages: list[Message], 
    window: int,
    working_dir: Path,
    think: bool = False
) -> AsyncGenerator[AgentStreamResponse, None]:
    """
    The entrypoint for the Bluegill agent. Streams the agent's response and tool 
    executions in response to the given message chain.
    """
    
    def create_message(role: Role, content: str | None) -> None:
        """
        Adds a message to the growing agent context.
        """
        
        message = Message(role=role, content=content or "")
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
            context=(messages, [])
        )
        return
        
    if not messages:
        yield AgentStreamResponse(
            event="error",
            done=True,
            content="No messages received",
            total_duration=0,
            token_count=0,
            context=(messages, [])
        )
        return    
        
    full_context = messages.copy()
    new_context: list[Message] = []
    total_duration = 0
    token_count = 0
    i = 0
    
    MARKER = "[TOOL]"
    END_MARKER = "[/TOOL]"
    KEEP = max(len(MARKER), len(END_MARKER)) - 1

    for i in range(MAX_ITERATIONS):
        buffer_str = ""             # stores incoming chunks
        tool_buffer_str = ""        # stores chunks within the same tool call
        tool_calls = []             # list of complete tool call strings
        tool_call = False           # True if currently consuming tool call chunks
        model_response = ""         # the model's response stripped of tool calls
        stream_complete = False     # True if a 'done' chunk is received
        
        try:
            async for chunk in provider.stream(
                model=model,
                messages=full_context,
                system_prompt=SYSTEM_PROMPT, 
                window=window,
                think=think
            ):
                if chunk.done:
                    # retrieve query duration and token usage from 'done' chunk
                    total_duration += chunk.total_duration or 0
                    token_count += chunk.token_count or 0
                    stream_complete = True
                    
                    # yield an error if the model returns a single empty chunk (no response)
                    if not any([model_response, tool_calls, buffer_str, tool_buffer_str, not chunk.response == ""]):
                        create_message("system", "No response from model")
                        
                        yield AgentStreamResponse(
                            event="error",
                            done=True,
                            content="No response from model",
                            total_duration=total_duration,
                            token_count=token_count,
                            context=(messages, new_context)
                        )
                        return
                
                # yield thinking chunks
                if chunk.thinking:
                    yield AgentStreamResponse(
                        event="thinking",
                        content=chunk.thinking,
                    )
                    continue
                
                buffer_str += chunk.response
                
                while True:
                
                    if not tool_call: # a tool call has not been detected yet
                        idx = buffer_str.find(MARKER)

                        if idx != -1: # if [TOOL] is found
                            
                            if idx: 
                                # if there is text before the tool call
                                # then separate and yield it
                                text = buffer_str[:idx]
                                model_response += text
                                
                                yield AgentStreamResponse(
                                    event="generate",
                                    content=text
                                )

                            # wwitch into tool call parsing mode
                            tool_call = True
                            
                            # put start of tool_call into tool_buffer_str
                            tool_buffer_str = buffer_str[idx:]
                            
                            # flush standard buffer
                            buffer_str = ""

                            # jump to tool parsing else block below
                            continue
                            
                        # no tool call is found so yield part of buffer_str
                        # that definitely does not contain part of a tool call
                        if len(buffer_str) > KEEP:
                            emit = buffer_str[:-KEEP]
                            model_response += emit

                            yield AgentStreamResponse(
                                event="generate",
                                content=emit
                            )

                            buffer_str = buffer_str[-KEEP:]

                        break
                    
                    else: # currently parsing a tool call
                        tool_buffer_str += buffer_str
                        buffer_str = ""
                        
                        # look for end of tool call
                        idx = tool_buffer_str.find(END_MARKER)

                        if idx != -1: # if [/TOOL] exists
                            # save complete tool call
                            tool_buffer_str, _, buffer_str = tool_buffer_str.partition(END_MARKER)
                            tool_calls.append(tool_buffer_str + END_MARKER)

                            # exit tool parsing mode
                            tool_call = False
                            tool_buffer_str = ""
                            
                            # go to start of while loop and parse remaining non-tool call text
                            continue
                        
                        # if '[/TOOL]' doesn't exist then get next chunk
                        break
                    
        except ProviderError as e:
            create_message("system", str(e))
            
            yield AgentStreamResponse(
                event="error",
                done=True,
                content=str(e),
                total_duration=total_duration,
                token_count=token_count, 
                context=(messages, new_context)
            )
            return
        
        if buffer_str:
            model_response += buffer_str
            yield AgentStreamResponse(
                event="generate",
                content=buffer_str
            )
            
        if model_response:
            create_message("assistant", model_response)
            
        if tool_call:
            yield AgentStreamResponse(
                event="error",
                content="Stream ended with an incomplete tool call"
            )
        
        if not stream_complete:
            create_message("system", "Provider stream ended unexpectedly")
            
            yield AgentStreamResponse(
                event="error",
                done=True,
                content="Provider stream ended unexpectedly",
                total_duration=total_duration,
                token_count=token_count,
                context=(messages, new_context)
            )
            return
                
        if tool_calls: # enter tool call chain
            
            # parse and execute each tool call
            for t in tool_calls:
                tool_name = None
                tool_input = None
                tool_call_raw = None

                try:
                    response = _parse_tool_call(t) # parse the tool call

                    tool_name = response.tool
                    tool_input = response.input
                    tool_call_raw = response.content

                    create_message("assistant", tool_call_raw)

                    # yield the models's tool call
                    yield response 

                    tool = TOOLS.get(tool_name) if tool_name else None

                    if not tool:
                        raise ToolNotFoundError(f"'{tool_name}' tool does not exist")

                    tool_result = await tool.run(tool_input, working_dir) 
                    create_message("tool", tool_result)

                    # yield the result of the tool call
                    yield AgentStreamResponse( 
                        event="tool_result",
                        content=tool_result,
                        tool=tool_name,
                        input=tool_input
                    )
                
                except ToolNotFoundError:
                    create_message("system", f"{tool_name} does not exist\nAgent response: {t}")

                    yield AgentStreamResponse(
                        event="error",
                        content=f"'{tool_name}' tool does not exist\nAgent response: {t}"
                    )
                
                except ToolExecutionError as e:
                    create_message("system", f"An error was encountered when trying to run tool '{tool_name}': {e}\nAgent response: {t}")

                    yield AgentStreamResponse(
                        event="error",
                        content=f"An error was encountered when trying to run tool '{tool_name}': {e}\nAgent response: {t}"
                    )
                
                except SafePathError as e:
                    create_message("system", f"Error running tool '{tool_name}': {e}\nAgent response: {t}")

                    yield AgentStreamResponse(
                        event="error",
                        content=f"Error running tool '{tool_name}': {e}\nAgent response: {t}"
                    )
                
                except JSONParseError:
                    create_message(
                        "system", 
                        f"Assistant provided malformed tool call: {t}"
                    )

                    yield AgentStreamResponse(
                        event="error",
                        content=f"Assistant provided malformed tool call: {t}"
                    )

                except Exception:
                    create_message("system", f"An unexpected error occurred\nAgent response: {t}")

                    yield AgentStreamResponse(
                        event="error",
                        content=f"An unexpected error occurred\nAgent response: {t}"
                    )
            
        else: 
            # if no tool calls then terminate the stream
            yield AgentStreamResponse(
                done=True,
                total_duration=total_duration,
                token_count=token_count,
                context=(messages, new_context)
            )
            return
    
    if i == MAX_ITERATIONS - 1: # max iterations reached
        yield AgentStreamResponse(
            event="error",
            done=True,
            content="Max steps reached",
            total_duration=total_duration,
            token_count=token_count,
            context=(messages, new_context)
        ) 
        return
           