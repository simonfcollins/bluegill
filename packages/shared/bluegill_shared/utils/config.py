from pathlib import Path
import json
from pydantic import BaseModel, ValidationError


BASE_DIR = Path.home() / ".bluegill"
BASE_DIR.mkdir(exist_ok=True)

CONFIG_FILE = BASE_DIR / "config.json"


class Workspace(BaseModel):
    """
    Represents a workspace on the user's local machine that can be accessed by the Agent.
    
    Attributes:
        name: The name of the workspace. Can be anything.
        
        path: The absolute path to the workspace directory on the host machine.
    """
    
    name: str
    path: str


class Provider(BaseModel):
    """
    Represents an LLM provider.
    
    Attributes:
        provider: The common name of the provider.
        
        url: The URL of the provider's API. 
        
        api_key: A personal API key token required to access the provider API.
    """
    
    name: str
    url: str
    api_key: str | None = None
    
    
class Model(BaseModel):
    """
    Represents an LLM.
    
    Attributes:
        name: The common name of this model's provider.
        
        model: The name of the model (e.g. 'qwen3.5:9b').
        
        window: The context window size. Defaults to 8000 tokens.
    """
    
    provider: str
    name: str
    window: int = 8000
    
    
class Config(BaseModel):
    """
    Represents the global config.json file.
    
    Attributes:
        workspaces: A list of user defined, Agent accessible workspaces.
        
        providers: A list of providers.
        
        Models: A list of language models.
    """
    
    workspaces: list[Workspace]
    providers: list[Provider]
    models: list[Model]
    

def format_config_error(e: ValidationError) -> str:
    """
    Formats pydantic Validation Errors that result from an invalid config file.
    """
    
    lines = ["Invalid config file:\n"]

    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"])
        msg = err["msg"]
        val = err.get("input")

        lines.append(f"- {loc}: {msg} (got {val})")

    return "\n".join(lines)


def load_config() -> Config:
    """
    Loads the global config.json file located in $HOME/.bluegill.
    """
    if not CONFIG_FILE.exists():
        return Config(workspaces=[], providers=[], models=[])

    with CONFIG_FILE.open("r") as f:
        data = json.load(f)

    try:
        return Config.model_validate(data)

    except ValidationError as e:
        raise RuntimeError(format_config_error(e)) from e
        