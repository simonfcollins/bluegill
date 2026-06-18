from pathlib import Path
import json
from pydantic import BaseModel, ValidationError, Field


BASE_DIR = Path.home() / ".bluegill"
BASE_DIR.mkdir(exist_ok=True)

CONFIG_FILE = BASE_DIR / "config.json"


class Workspace(BaseModel):
    """
    Represents a workspace on the user's local machine that can be accessed by the Agent.
    
    Attributes:
        id: A unique identifier for this workspace. 

        name: The name of the workspace. Can be anything.
        
        path: The absolute path to the workspace directory on the host machine.
    """
    
    id: str
    name: str
    path: Path


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
    
    
class Compact(BaseModel):
    """
    Represents compaction behavior of the agent.
    
    Attributes:
        enabled: True for automatic compaction of the session context.
        
        threshold: The percentage of context usage at which to trigger compaction.
    """
    
    enabled: bool = True
    threshold: float = 0.9


class Agent(BaseModel):
    """
    Represents attributes and functionality of the agent.
    
    Attributes:
        compact: A Compact object containing compaction behavior.
    """
    
    compact: Compact = Field(default_factory=Compact)
    
        
class Config(BaseModel):
    """
    Represents the global config.json file.
    
    Attributes:
        workspaces: A dict of user defined, Agent accessible workspaces.
        
        providers: A dict of providers.
        
        models: A dict of language models.

        agent: An Agent.
    """
    
    workspaces: dict[str, Workspace] = {}
    providers: dict[str, Provider] = {}
    models: list[Model] = []
    agent: Agent = Field(default_factory=Agent)


    def get_model(self, model: str, provider: str) -> Model | None:
        """
        Retrieves the model as described by the given model and provider names.
        """

        return next(
            (
            m 
            for m in self.models 
            if m.name == model and m.provider == provider    
            ), None
        )
    

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
    if not CONFIG_FILE.exists():
        return Config()

    with CONFIG_FILE.open("r") as f:
        data = json.load(f)

    try:
        return Config.model_validate({
            "workspaces": {
                w["id"]: w
                for w in data.get("workspaces", [])
            },
            "providers": {
                p["name"]: p
                for p in data.get("providers", [])
            },
            "models": data.get("models", []),
            "agent": data.get("agent", {}),
        })

    except ValidationError as e:
        raise RuntimeError(format_config_error(e)) from e
