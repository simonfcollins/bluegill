# Bluegill Agent SDK

A lightweight Python SDK for interacting with the Bluegill API. This SDK provides a simple interface for managing sessions and querying language models via supported providers.

---

## Features

* Session management (create, load, clear, list)
* Persistent conversation history
* Streaming text generation interface
* Provider and model configuration
* Automatic message tracking
* Async streaming responses
* Supports the following LLM providers: 'Ollama'

---

## Installation

```bash
pip install httpx
```

Ensure you also have access to the Bluegill API server.

---

## Quick Start

```python
import asyncio
from agent import Agent

async def main():
    agent = Agent(
        api_url="http://localhost:54345",
        provider="ollama",
        model="qwen3-coder:latest"
    )

    workspaces = agent.workspaces

    if workspaces:
        # Create a new session (workspace required)
        agent.new_session(workspace_id=workspaces[0].id)

    # Stream a response
    async for chunk in agent.chat_stream("Hello, how are you?"):
        print(chunk.content, end="")

    agent.close()

asyncio.run(main())
```

---

## Configuration

### Agent Parameters

| Parameter  | Type | Description |
| ---------- | ---- | ---------------------------------------------- |
| api_url    | str  | URL of the Bluegill API |
| provider   | str  | Model provider (currently supports: `ollama`) |
| model      | str  | Model name |
| session_id | str  | Existing session ID (optional) |
| timeout    | int  | Request timeout in seconds |

---

## Core Methods

### get_sessions()

Retrieve all available sessions.

```python
sessions = agent.get_sessions()
```

---

### new_session(workspace_id)

Create and activate a new session in a workspace.

```python
session = agent.new_session(workspace_id="workspace-id")
```

Returns a `Session`.

---

### load_session(session_id)

Load a session by session ID.

```python
success = agent.load_session("session-id")
```

Returns:
- True if successfully loaded
- False otherwise

---

### load_last_session()

Load the most recently used session.

```python
agent.load_last_session()
```

---

### clear_session()

Clear conversation history of the active session.

```python
agent.clear_session()
```

---

### chat_stream(prompt, think=False)

Send a prompt to the model and receive a streamed response.

```python
async for chunk in agent.chat_stream("Explain recursion", think=False):
    print(chunk.content, end="")
```

Returns an AsyncGenerator[AgentStreamResponse, None].

---

### dump(session_id)

Retrieve full session message history.

```python
messages = agent.dump(session_id="session-id")
```

Returns list[Message].

---

### service_running()

Check if the Bluegill API service is running.

```python
agent.service_running()
```

---

### close()

Close the HTTP client.

```python
agent.close()
```

---

## Properties

### provider

Get or set the model provider.

```python
agent.provider = `ollama`
```

---

### session_id

Get or set the active session ID.

```python
agent.session_id = `your-session-id`
```

---

### messages

Returns the locally stored message history.

```python
history = agent.messages
```

---

### workspaces

List available workspaces from server config.

```python
workspaces = agent.workspaces
```

---

## Error Handling

* HTTP and API errors raise `AgentError`.
* Missing resources raise `NotFoundError`.
* Stream validation failures emit an error event in the stream.

Example:

```python
async for chunk in agent.chat_stream("Hello"):
    if chunk.event == "error":
        print("Error:", chunk.content)
```

---

## Notes

* Ensure the Bluegill API is running before making requests.
* Session state is maintained server-side.
* Messages are cached locally in the Agent instance.
* chat_stream() requires an active session, provider, model, and workspace.
* Streaming is async-only.

---

## License

MIT License
