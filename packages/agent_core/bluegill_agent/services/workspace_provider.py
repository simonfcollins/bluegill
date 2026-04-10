from pathlib import Path

class WorkspaceProvider:
    _workspace_root: Path = None
    
    @classmethod
    def initialize(cls, workspace_dir: str) -> None:
        """
        Initialize the workspace directory, creating it if necessary.

        Args:
            workspace_dir (str): Path to the workspace (supports '~').
        """
        workspace = Path(workspace_dir).expanduser().resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        cls._workspace_root = workspace
        
    @classmethod
    def get_workspace(cls) -> Path:
        """
        Get the workspace root path.
        
        Returns:
            Path: Workspace root.

        Raises:
            RuntimeError: If the workspace is not initialized.
        """
        if cls._workspace_root is None:
            raise RuntimeError("WorkspaceProvider is not initialized.\n" +
                               "Use: \'WorkspaceProvider.initialize(\"workspace/path/\")\'")
        return cls._workspace_root
    
    @classmethod
    def resolve(cls, *paths) -> Path:
        """
        Resolve relative paths under the workspace root.

        Args:
            *paths: Path components relative to workspace.

        Returns:
            Path: Absolute resolved path.

        Example:
            config = WorkspaceProvider.resolve("configs", "settings.yaml")
        """
        return cls.get_workspace().joinpath(*paths).resolve()
