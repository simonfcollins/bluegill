from asyncio import CancelledError
from pathlib import Path

from textual.app import App, ComposeResult
from textual import on
from textual.widgets import Static, Footer, Label
from textual.containers import Horizontal
from textual.binding import Binding

from bluegill_sdk import Agent, AgentError, NotFoundError

from widgets.chat_view import ChatView
from widgets.chat_input import ChatInput
from widgets.item_select_modal import ItemSelectModal
from widgets.info_bar import InfoBar
from widgets.confirm import Confirm


class Bluegill(App):
    
    CSS_DIR = Path(__file__).parent / "css"
    
    CSS_PATH = [str(path) for path in sorted(CSS_DIR.glob("*.tcss"))]
    
    BINDINGS = [
        Binding(key="ctrl+q", action="quit", description="Quit"),
        Binding("ctrl+s", "stop_agent", "Stop"),
        Binding("ctrl+r", "show_commands", "Commands")
    ]
    

    def __init__(self) -> None:
        super().__init__()
        
        self.agent_worker = None
        
        # initialize agent
        self.agent = Agent()
        self.context_size = 0
        
        if not self.agent.service_running():
            print(f"Bluegill service unavailable at '{self.agent.api_url}'. Are you sure it's running?")
            self.exit()
            return
        
        try:
            self.agent.load_config()
            
        except AgentError as e:
            print(f"Error communicating with the Bluegill service:\n{e}")
        
        if self.agent.models:
            self.agent.provider = self.agent.models[0].provider
            self.agent.model = self.agent.models[0].name   
            self.context_size = self.agent.models[0].window
        
        try:
            # load previous session
            self.agent.load_last_session()
            
        except NotFoundError:
            pass
            
        except AgentError:
            raise


    #==================================================
    #                  LIFECYCLE
    #==================================================
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="title_bar"):
            yield Static("><> Bluegill", id="title")
            yield Label(self.agent.session_name, id="session-name", classes="label")
        yield ChatView(id="chat", classes="chat-view")
        yield ChatInput(id="input", placeholder="Code anything or run a command with '/...'")
        yield InfoBar(id="info-bar")
        yield Footer()


    def on_mount(self) -> None:
        self.chat_view = self.query_one("#chat", ChatView)
        self.input = self.query_one("#input", ChatInput)
        self.info_bar = self.query_one("#info-bar", InfoBar)
        self.session_name_label = self.query_one("#session-name", Label)
        
        self.info_bar.update(
            token_window=int(self.context_size) or None,
            tokens_used=0,
            model=f"{self.agent.model} - {self.agent.provider}" if self.agent.model else None
        )
        
        self._change_session(self.agent.session_id)
        
        self.input.focus()
        
        if not self.agent.model:
            self.notify(
                title="No model selected!", 
                message="Define models in '~/.bluegill/config.json'.",
                severity="warning",
                timeout=15
            )
            
        if not self.agent.workspaces:
            self.notify(
                title="No workspaces available!", 
                message="Define workspaces in '~/.bluegill/config.json'.",
                severity="warning",
                timeout=15
            )


    #==================================================
    #                 EVENT HANDLERS
    #==================================================
    
    @on(ChatInput.Submitted)
    def _on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """
        Handles the event in which the user enters a chat query.
        """
        
        # get the user query from the input
        text = event.value.strip()
        event.input.text = ""
        
        # check for and handle commands
        if text.startswith("/"):
            self.run_worker(self._handle_command(text))
            return
        
        if not self.agent.session_id:
            self.notify(
                title="No session selected!", 
                message="Use '/new' to create a new session.",
                severity="warning"
            )
            return
        
        # verify that a model is selected
        if not self.agent.provider or not self.agent.model:
            self.notify(
                title="No model selected!", 
                message="Define models in '~/.bluegill/config.json'.",
                severity="warning",
                timeout=15
            )
            return

        # disable chat input and other interactions
        self._lock_interactions(True)

        # add the user message to the chat view
        self.chat_view.add_message("user", text)

        # enter the agent streaming loop
        self.agent_worker = self.run_worker(self._stream_agent(text), exclusive=True)
 

    #==================================================
    #                  APP ACTIONS
    #==================================================

    def action_stop_agent(self) -> None:
        """
        A textual action for stopping agent generation.
        Bound to ctrl+s
        """
        
        if self.agent_worker and self.agent_worker.is_running:
            self.agent_worker.cancel()
            self.notify("Generation stopped.")

        self._lock_interactions(False)
        self.input.focus()
        
        
    def action_show_commands(self) -> None:
        """
        A textual action for showing the agent specific command pallet.
        """
        
        self.run_worker(self._show_commands())
        
        
    #==================================================
    #                   HELPERS
    #==================================================
    
    async def _handle_command(self, command: str) -> None:
        """
        Parses and handles user commands.
        """

        match command:
            case "/new": # create a new session
                await self._handle_new_session_command()
                
            case "/clear": # clear the context for the current session
                self._handle_clear_session_command()
            
            case "/session": # change active session
                await self._handle_change_session_command()
                
            case "/model": # change model
                await self._handle_change_model_command()
                
            case "/delete":
                await self._handle_delete_session_command()

            case _:
                self.notify("Command not found.", severity="warning")
                
        self._lock_interactions(False)
        self.input.focus()
                

    def _change_session(self, session_id: str | None) -> None:
        """
        Updates the DOM accordingly in the event of a session change.
        """
        
        try: 
            # update the agent
            self.agent.session_id = session_id
        
        except AgentError as e:
            self._handle_agent_error(e)
            return
        
        # clear the chat
        self.chat_view.clear()
        
        # add the new active session messages to the chat view
        for m in self.agent.messages:
            self.chat_view.add_message(m.role, m.content)
            
        # update DOM elemenets to reflect the session change
        self.info_bar.update(
            tokens_used=self.agent.tokens_used,
            workspace=self.agent.workspace_id,
        )
        self.session_name_label.update(self.agent.session_name or "No Session Selected")
    
    
    async def _show_commands(self) -> None:
        """
        The actual logic behind the show_commands action.
        """
        
        command = await self.push_screen_wait(
            ItemSelectModal(
                {
                    "/model": "[bold]/model[/bold]\n[dim]change models[/dim]",
                    "/session": "[bold]/session[/bold]\n[dim]change sessions[/dim]",
                    "/new": "[bold]/new[/bold]\n[dim]start a new session[/dim]",
                    "/clear": "[bold]/clear[/bold]\n[dim]clear the current session[/dim]",
                    "/delete": "[bold]/delete[/bold]\n[dim]delete session[/dim]",
                },
                "Select command"
            )
        )

        if command is None:
            return
            
        self.input.text = command
        
        
    def _lock_interactions(self, lock: bool) -> None:
        """
        Disables or enables interactive elements.
        """
        
        self.input.disabled = lock
        self.info_bar.thinking_switch.disabled = lock
        
        
    def _handle_agent_error(self, e: AgentError) -> None:
        """
        Displays bluegill_sdk.AgentErrors in a Toast.
        """
        
        self.notify(str(e), title=e.message, severity="error")
        
        
    #==================================================
    #                COMMAND HANDLERS
    #==================================================
    
    async def _handle_new_session_command(self) -> None:
        """
        Handler for the '/new' command.
        """
        
        # prompt the user to select the workspace for the new session
        workspace_id = await self.push_screen_wait(
            ItemSelectModal({ws.id: ws.name for ws in self.agent.workspaces}, "Select Workspace")
        )
    
        if workspace_id is None:
            return

        try:
            self.agent.new_session(workspace_id)

        except AgentError as e:
            self._handle_agent_error(e)
            return

        self.chat_view.clear()

        self.info_bar.update(
            tokens_used=self.agent.tokens_used,
            workspace=self.agent.workspace_id,
        )
        self.session_name_label.update(self.agent.session_name)

        self.notify("New session created.")
    
    
    def _handle_clear_session_command(self) -> None:
        """
        Hanlder for the '/clear' command.
        """
        
        if not self.agent.session_id:
            self.notify("No session selected!", severity="warning")
            return
        
        try:
            self.agent.clear_session()
            
        except AgentError as e:
            self._handle_agent_error(e)
            return
            
        self.info_bar.tokens_used = 0
        self.chat_view.clear()
        self.notify("Session cleared.")

    
    async def _handle_change_session_command(self) -> None:
        """
        Handler for the '/session' command.
        """
        
        try:
            sessions = self.agent.get_sessions()
        
        except AgentError as e:
            self._handle_agent_error(e)
            return
        
        session_id = await self.push_screen_wait(
            ItemSelectModal({s.id: s.name for s in sessions}, "Select Session")
        )

        if session_id is None:
            return
        
        self._change_session(session_id)
    
    
    async def _handle_change_model_command(self) -> None:
        """
        Handler for the '/model' command.
        """
       
        model_id = await self.push_screen_wait(
            ItemSelectModal(
                {
                    f"{m.provider},{m.name},{m.window}": f"{m.name} - {m.provider}" 
                    for m in self.agent.models
                },
            "Select Model")
        )

        if model_id is None:
            return

        self.agent.provider, self.agent.model, window = model_id.split(",")
        self.context_size = int(window)

        self.info_bar.update(
            token_window=self.context_size,
            model=f"{self.agent.model} - {self.agent.provider}"
        )


    async def _handle_delete_session_command(self) -> None:
        """
        Handler for the '/delete' command.
        """

        try:
            sessions = self.agent.get_sessions()
        
        except AgentError as e:
            self._handle_agent_error(e)
            return
        
        session_id = await self.push_screen_wait(
            ItemSelectModal({s.id: s.name for s in sessions}, "Delete Session")
        )

        if session_id is None:
            return
        
        session = next(
            (
                s for s in sessions if s.id == session_id
            ), None
        )

        if session is None:
            return

        value = await self.push_screen_wait(
            Confirm(
                f"Are you want to delete session\n[bold]'{session.name}'[/bold]?"
            )
        )

        if value:
            # save the current agent session_id
            old_session_id = self.agent.session_id

            # delete the chosen session
            try:    
                self.agent.delete_session(session_id)

            except AgentError as e:
                self._handle_agent_error(e)
                return

            if old_session_id == session_id:
                try:
                    self.agent.load_last_session()
                    self._change_session(self.agent.session_id)

                except NotFoundError as e:
                    self._change_session(None)

                except AgentError as e:
                    self._handle_agent_error(e)
                    return

            self.notify("Session deleted.")

        
    #==================================================
    #              AGENT STREAMING LOGIC
    #==================================================
    
    async def _stream_agent(self, prompt: str) -> None:
        """
        Queries the agent then accumulates and renders the response chunks.
        """
        
        first_chunk = True
        event = None
        current_widget = None
        parts = []
        
        placeholder = self.chat_view.add_message("thinking", "Thinking...")
        
        try:
            async for chunk in self.agent.chat_stream(prompt, self.info_bar.thinking):
                
                # remove the placeholder when the first chunk arrives
                if first_chunk:
                    placeholder.remove()
                    first_chunk = False

                # chunk event changing indicates breaks between messages
                if chunk.event and chunk.event != event:
                    
                    # call the final render on the current accumulating widget
                    if current_widget:
                        current_widget.render_final()
                    
                    # create new current widget
                    current_widget = self.chat_view.add_message(chunk.event, chunk.content)
                    parts = []
                
                event = chunk.event

                # accumulate new chunk content in current widget
                if chunk.content:
                    parts.append(chunk.content)
                    
                    # re-render current widget with new content
                    if current_widget:
                        current_widget.update("".join(parts))
                        self.chat_view.scroll_end()

                # call final render on the current widget (doesn't trigger above)
                if chunk.done and current_widget:
                    current_widget.render_final()

        except CancelledError:
            # incase of stop_agent command
            placeholder.remove()
        
        except AgentError as e:
            self._handle_agent_error(e)

        finally:
            # clean up and reset UI for next query
            self.chat_view.scroll_end()
            self._lock_interactions(False)
            self.input.focus()
            self.current_worker = None
            self.info_bar.tokens_used = self.agent.tokens_used
            self.session_name_label.update(self.agent.session_name)
            
        
if __name__ == "__main__":
    app = Bluegill()
    app.run()
