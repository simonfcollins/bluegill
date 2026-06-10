import subprocess
from pathlib import Path
from bluegill_shared.utils import Config, load_config


BASE_DIR = Path.home() / ".bluegill"
BASE_DIR.mkdir(exist_ok=True)

# reference to the default agent workspace on the host
DEFAULT_WORKSPACE = BASE_DIR / "default-workspace"

DOCKER_USER = "assistant"

# reference to the base workspaces directory in the Docker container
DOCKER_BASE_DIR = Path(f"/home/{DOCKER_USER}/workspaces/")

DOCKER_IMAGE = "bluegill_agent:latest"


def load_workspace_dirs() -> list[Path]:
    """
    Reads the config.json file and returns the list of workspace paths.
    """

    cfg: Config = load_config()
        
    return [Path(ws.path).expanduser().resolve() for ws in cfg.workspaces]


def verify_docker() -> bool:
    """
    Returns True if Docker is installed on the host. False otherwise.
    """

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


def verify_image() -> bool:
    """
    Returns True if the bluegill_agent:latest Docker image exists.
    False otherwise.
    """

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
    

def pull_docker_image() -> str:
    """
    Retrieves the latest version of the bluegill_agent Docker image.
    """

    # pull the latest version of the bluegill_agent image
    result = subprocess.run(
        ["docker", "pull", "ghcr.io/simonfcollins/bluegill_agent:latest"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to pull image:\n{result.stderr}")
    
    # rename the image
    subprocess.run(
    [
        "docker", "tag",
        "ghcr.io/simonfcollins/bluegill_agent:latest",
        f"{DOCKER_IMAGE}"
    ],
    check=True
    )

    return result.stdout


def launch_agent() -> None:
    """
    Launch a Docker container from the bluegill_agent:latest image. 
    Verifies that Docker is installed, pulls the image, and defines bind mounts
    from the config.json file.
    """

    # check if Docker is installed
    if not verify_docker():
        print("Error: dependency \'docker\' is not installed")
        return
    
    # pull the bluegill_agent Docker image if it doesn't exist locally
    if not verify_image():
        try:
            pull_docker_image()
        except RuntimeError as e:
            print(e)
            return
        
    
    # if the image still doesn't exist, exit
    if not verify_image():
        print(f"Error: unable to retrieve image \'{DOCKER_IMAGE}\'")
        return
        
    # prepare the workspaces for bind mounting
    mounts = []
    workspace_dirs = load_workspace_dirs()
    
    # default workspace
    DEFAULT_WORKSPACE.mkdir(exist_ok=True)
    mounts.extend(["-v", f"{DEFAULT_WORKSPACE}:{DOCKER_BASE_DIR / 'default-workspace'}"])

    # user-defined workspaces
    for d in workspace_dirs:
        mounts.extend(["-v", f"{Path(d).expanduser().resolve()}:{DOCKER_BASE_DIR / Path(d).name}"])
        
    # docker launch command
    cmd = [
        "docker", "run", "--rm",
        "--network=host",
        "-v", f"{BASE_DIR}:/home/{DOCKER_USER}/.bluegill",
        *mounts,
        DOCKER_IMAGE
    ]
    
    try:
        print("Launching agent:\n", " ".join(cmd))
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("Agent stopped")
    

if __name__ == "__main__":
    launch_agent()
