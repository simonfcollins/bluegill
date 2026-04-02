import subprocess
from pathlib import Path
import json
from bluegill_sdk.utils.config import *

BASE_DIR = Path.home() / ".bluegill"
BASE_DIR.mkdir(exist_ok=True)

DEFAULT_WORKSPACE = BASE_DIR / "workspace"

DOCKER_BASE_DIR = Path("/mnt/workspaces/")

DOCKER_IMAGE = "bluegill_agent:latest"

def load_workspace_dirs() -> List[Path]:
    cfg: Config = load_config()
        
    workspaces = []
    for ws in cfg["workspaces"]:
        path = Path(ws["path"]).expanduser().resolve()
        workspaces.append(path)
        
    return workspaces

def verify_docker():
    try:
        result = subprocess.run(
            [
                "docker", "--version"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False

def verify_image():
    try:
        result = subprocess.run(
            [
                "docker", "image", "ls",
                "--filter", f"reference={DOCKER_IMAGE}",
                "-q"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False
    
def pull_docker_image():
    result = subprocess.run(
        ["docker", "pull", "ghcr.io/simonfcollins/bluegill_agent:latest"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to pull image:\n{result.stderr}")
    
    subprocess.run(
    [
        "docker", "tag",
        "ghcr.io/simonfcollins/bluegill_agent:latest",
        f"{DOCKER_IMAGE}"
    ],
    check=True
    )

    return result.stdout

def launch_agent():
    if not verify_docker():
        print("Error: dependency \'docker\' is not installed")
        return
    
    if not verify_image():
        try:
            pull_docker_image()
        except RuntimeError as e:
            print(e)
            return
        
    if not verify_image():
        print(f"Error: unable to retrieve image \'{DOCKER_IMAGE}\'")
        return
        
    mounts = []
    workspace_dirs = load_workspace_dirs()
    
    if len(workspace_dirs) == 0:
        DEFAULT_WORKSPACE.mkdir(exist_ok=True)
        mounts.extend(["-v", f"{DEFAULT_WORKSPACE}:{DOCKER_BASE_DIR / 'workspace'}"])
    else:
        for d in workspace_dirs:
            mounts.extend(["-v", f"{Path(d).expanduser().resolve()}:{DOCKER_BASE_DIR / Path(d).name}"])
        
    cmd = [
        "docker", "run", "--rm",
        "--network=host",
        "-v", f"{BASE_DIR}:/home/agentuser/.bluegill",
        *mounts,
        DOCKER_IMAGE
    ]
    
    print("Launching agent:", " ".join(cmd))
    subprocess.run(cmd)

if __name__ == "__main__":
    launch_agent()