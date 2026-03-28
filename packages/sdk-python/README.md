# Bluegill Python SDK

A lightweight async Python client for interacting with the Bluegill API.

## Features
- Async-first API (httpx)
- Session-based conversations
- Simple text generation interface
- Automatic connection reuse

## Installation 

Build the package from source:

```bash
cd .../bluegill/packages/sdk-python
pip install .
```

## Quick Start
```python
import asyncio
from bluegill_sdk import Agent

async def main():
    agent = Agent(
        provider="ollama",
        model="qwen3-coder:latest",
    )

    # create a session
    await agent.create_session()

    # generate text
    response = await agent.generate("Hello!")
    print(response)

    # clear session
    await agent.clear_session()

    await agent.close()

asyncio.run(main())
```

## Providers

Bluegill currently only supports local models from Ollama.

