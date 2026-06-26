from textual.containers import Container, Horizontal
from textual.widgets import Label, ProgressBar, Switch
from textual.app import ComposeResult


class InfoBar(Container):
    """
    Container widget displaying information about the agent and session.
    """
    
    def __init__(
        self,
        id: str,
        token_window: int | None = None,
        tokens_used: int | None = None,
        workspace: str | None = None,
        model: str | None = None,
        **xargs,
    ) -> None:
        super().__init__(id=id, **xargs)

        self._token_window = token_window
        self._tokens_used = tokens_used
        self._workspace = workspace
        self._model = model

        self._token_bar = ProgressBar(show_eta=False, show_percentage=True, classes="token-bar")
        self._workspace_label = Label("[dim]Workspace[/dim]", classes="info-bar-item")
        self._model_label = Label("[dim]Model[/dim]", classes="info-bar-item")
        self._thinking_switch = Switch(value=False, name="Thinking", classes="thinking-switch")
    

    def compose(self) -> ComposeResult:
        with Horizontal(classes="info-bar-horizontal"):
            yield self._model_label
            yield self._workspace_label
            with Horizontal(classes="info-bar-horizontal info-bar-item"):
                yield Label("[dim]Show thinking[/dim]", classes="info-bar-label") 
                yield self._thinking_switch
        with Horizontal(classes="info-bar-usage"):
            yield Label("[dim]Usage[/dim]", classes="info-bar-label")
            yield self._token_bar
        

    def on_mount(self) -> None:
        self.update(
            self._token_window,
            self._tokens_used,
            self._workspace,
            self._model,
        )
        
        
    def update(
        self,
        token_window: int | None = None,
        tokens_used: int | None = None,
        workspace: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Bulk update method.
        """
        
        if token_window is not None:
            self.token_window = token_window

        if tokens_used is not None:
            self.tokens_used = tokens_used

        if workspace is not None:
            self.workspace = workspace

        if model is not None:
            self.model = model


    #==================================================
    #               WIDGET PROPERTIES
    #==================================================

    @property
    def token_bar(self) -> ProgressBar:
        return self._token_bar


    @property
    def workspace_label(self) -> Label:
        return self._workspace_label


    @property
    def model_label(self) -> Label:
        return self._model_label


    #==================================================
    #                DATA PROPERTIES
    #==================================================

    @property
    def token_window(self) -> int | None:
        return self._token_window


    @token_window.setter
    def token_window(self, value: int | None) -> None:
        self._token_window = value
        self._update_progress_bar()


    @property
    def tokens_used(self) -> int | None:
        return self._tokens_used


    @tokens_used.setter
    def tokens_used(self, value: int | None) -> None:
        self._tokens_used = value
        self._update_progress_bar()


    @property
    def workspace(self) -> str | None:
        return self._workspace


    @workspace.setter
    def workspace(self, value: str | None) -> None:
        self._workspace = value

        if value is None:
            self._workspace_label.update("[dim]Workspace[/dim]")
        else:
            self._workspace_label.update(
                f"[dim]Workspace[/dim] {value}"
            )


    @property
    def model(self) -> str | None:
        return self._model


    @model.setter
    def model(self, value: str | None) -> None:
        self._model = value

        if value is None:
            self._model_label.update("[dim]Model[/dim]")
        else:
            self._model_label.update(
                f"[dim]Model[/dim] {value}"
            )
            
    
    @property
    def thinking_switch(self) -> Switch:
        return self._thinking_switch
            
            
    @property
    def thinking(self) -> bool:
        return self._thinking_switch.value


    #==================================================
    #               INTERNAL HELPERS
    #==================================================

    def _update_progress_bar(self) -> None:
        if (
            self._token_window is not None
            and self._tokens_used is not None
        ):
            self._token_bar.update(
                total=self._token_window,
                progress=self._tokens_used,
            )
