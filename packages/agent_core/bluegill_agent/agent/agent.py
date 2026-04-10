import json
import re
from bluegill_agent.agent.tool_registry import TOOLS
from bluegill_agent.services.llm_service import LLMService
from bluegill_agent.services.session_manager import session_manager
from bluegill_agent.services.logger import get_logger
from bluegill_agent.agent.bootstrap_prompt import BOOTSTRAP_PROMPT
from bluegill_agent.exceptions.tool_exception import ToolExecutionError
from bluegill_agent.exceptions.agent_exception import JSONParseError
from bluegill_agent.exceptions.safe_path_exception import SafePathError
from typing import Any


def pretty(data) -> str:
    try:
        return json.dumps(data, indent=2)
    except:
        return str(data)
    
    
def parse_json(text) -> Any:
    # TODO : add robust JSON extraction
    try:
        cleaned = re.sub(r"```json|```", "", text).strip()
        data = json.loads(cleaned)
        return data
    except Exception:
        raise JSONParseError("Error parsing JSON.")


async def run_agent(provider: str, model: str, prompt: str, session_id: str):
    logger = get_logger(session_id)

    # ensure system prompt exists ONCE
    ensure_system_prompt(session_id)

    # initial user message
    response = await LLMService.generate(
        provider,
        model,
        [{"role": "user", "content": prompt}],
        session_id=session_id
    )

    for _ in range(20):

        try:
            data = parse_json(response)

            # tool call path
            if "tool" in data:
                tool_name = data["tool"]
                tool_input = data["input"]
                
                logger.info(f"[TOOL CALL] {tool_name} | input={pretty(tool_input)}")

                tool = TOOLS.get(tool_name)
                if not tool:
                    return f"Unknown tool: {tool_name}"
                   
                result = await tool.run(tool_input)
                logger.info(f"[TOOL RESULT] {result}")

                # send tool result back into session
                response = await LLMService.generate(
                    provider,
                    model,
                    [{"role": "tool", "content": result}],
                    session_id=session_id
                )
                continue
                
            # final response path
            if "response" in data:
                logger.info("No more tools to run")
                return data["response"]

            # fallback
            return response

        except ToolExecutionError as te:
            logger.error(f"[TOOL ERROR] Error executing tool: {te}")
            response = await LLMService.generate(
                    provider,
                    model,
                    [{"role": "tool", "content": f"An error was encountered when trying to run tool {tool_name}"}],
                    session_id
                )
            continue
        except SafePathError as se:
            logger.error(f"[SAFE PATH ERROR] {se}")
            response = await LLMService.generate(
                    provider,
                    model,
                    [{"role": "tool", "content": f"Invalid path for {tool_name} tool"}],
                    session_id
                )
            continue
        except JSONParseError as je:
            logger.error(f"[JSON ERROR] {je}")
            response = await LLMService.generate(
                    provider,
                    model,
                    [{"role": "system", "content": f"Your previous response was invalid JSON. You MUST output exactly one valid JSON object."}],
                    session_id
                )
            continue
        except Exception:
            logger.error("[ERROR] error processing query")
            return response

    return "Max steps reached"

def ensure_system_prompt(session_id) -> None:
    messages = session_manager.get_messages(session_id)

    if not any(m.role == "system" for m in messages):
        session_manager.add_message(session_id, "system", BOOTSTRAP_PROMPT)
