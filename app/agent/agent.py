import json
import re
from app.agent.tool_registry import TOOLS
from app.services.llm_service import LLMService
from app.services.session_manager import session_manager
from app.services.logger import get_logger
from app.agent.bootstrap_prompt import BOOTSTRAP_PROMPT


def pretty(data):
    try:
        return json.dumps(data, indent=2)
    except:
        return str(data)


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
            cleaned = re.sub(r"```json|```", "", response).strip()
            data = json.loads(cleaned)

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

        except Exception:
            # if parsing fails, just return raw model output
            logger.error("[ERROR] error processing query")
            response = await LLMService.generate(
                    provider,
                    model,
                    [{"role": "system", "content": f"An error was encountered when trying to run tool {tool_name}"}],
                    session_id=session_id
                )
            continue

    return "Max steps reached"

def ensure_system_prompt(session_id):
    messages = session_manager.get_messages(session_id)

    if not any(m["role"] == "system" for m in messages):
        session_manager.add_message(session_id, "system", BOOTSTRAP_PROMPT)