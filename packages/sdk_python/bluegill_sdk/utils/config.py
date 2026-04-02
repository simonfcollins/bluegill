from pathlib import Path
import json
from typing import TypedDict, List, Optional

BASE_DIR = Path.home() / ".bluegill"
BASE_DIR.mkdir(exist_ok=True)

CONFIG_FILE = BASE_DIR / "config.json"

class Workspace(TypedDict):
    name: str
    path: str

class Provider(TypedDict):
    provider: str
    url: str
    api_key: Optional[str]
    
class Model(TypedDict):
    provider: Provider
    model: str
    
class Config(TypedDict):
    workspaces: List[Workspace]
    providers: List[Provider]
    models: List[Model]

def load_config() -> Config:
    if not CONFIG_FILE.exists():
        return {
            "workspaces": [],
            "providers": [],
            "models": []
        }
    with CONFIG_FILE.open("r") as f:
        return json.load(f)