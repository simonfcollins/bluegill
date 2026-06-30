import subprocess
import platform
from pathlib import Path
import json
from bluegill_shared.utils import load_config, Config


BASE_DIR = Path.home() / ".bluegill"
BASE_DIR.mkdir(exist_ok=True)

# reference to the default agent workspace on the host
DEFAULT_WORKSPACE = BASE_DIR / "default-workspace"

DOCKER_USER = "assistant"

# reference to the base workspaces directory in the Docker container
DOCKER_BASE_DIR = Path(f"/home/{DOCKER_USER}/workspaces/")

DOCKER_IMAGE = "bluegill_agent:latest"


def is_docker_native() -> bool:
    try:
        result = subprocess.run(
            [
                "docker", "info", "--format", "{{.Name}}"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip() != "docker-desktop"

    except subprocess.CalledProcessError:
        return False
    

IS_DOCKER_NATIVE = is_docker_native()


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


def create_runtime_config() -> Config:
    """
    Creates a runtime config file for the Bluegill service.
    """
    
    src = BASE_DIR / "config.json"
    dst_dir = BASE_DIR / "runtime/"
    dst = dst_dir / "config.json"
    
    dst_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_config(src)

    if not IS_DOCKER_NATIVE:
        cfg = cfg.dockerize()

    dst.write_text(json.dumps(cfg.normalized(), indent=4))
    
    return cfg


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
    cfg = create_runtime_config()
    
    for w in list(cfg.workspaces.values()):
        mounts.extend(["-v", f"{Path(w.path).expanduser().resolve()}:{DOCKER_BASE_DIR / w.id}"])
        
    # docker launch command
    
    if IS_DOCKER_NATIVE:
        cmd = [
            "docker", "run", "--rm",
            "--network", "host",
            "-v", f"{BASE_DIR}:/home/{DOCKER_USER}/.bluegill",
            *mounts,
            DOCKER_IMAGE
        ]
        
    else:
        cmd = [
            "docker", "run", "--rm",
            "--add-host=host.docker.internal:host-gateway",
            "-p", "54345:54345",
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
