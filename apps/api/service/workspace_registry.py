from pathlib import Path

from bluegill_shared.utils import Workspace

class WorkspaceRegistry:
    """
    A global registry for user-defined agent workspaces.
    """
    
    def __init__(
        self,
        workspaces: list[Workspace],
        root: Path | None = None,
    ) -> None:
        """
        Args:
            workspaces: A list of Workspace objects.
            
            root: A directory path assumed to contain all workspaces in workspaces.
        """
    
        self._workspaces: dict[str, Workspace] = {}

        for workspace in workspaces:

            self._workspaces[workspace.id] = Workspace(
                id=workspace.id,
                name=workspace.name,
                path=(
                    root / workspace.id
                    if root
                    else workspace.path
                )
            )
            
            
    def get(self, workspace_id: str) -> Workspace:
        return self._workspaces[workspace_id]
    
    @property
    def workspaces(self) -> list[Workspace]:
        return list(self._workspaces.values())
