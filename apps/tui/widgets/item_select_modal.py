from typing import Generator
from textual.screen import ModalScreen
from textual.widgets import ListView, ListItem, Label
from textual.containers import Container
from textual.binding import Binding
from textual import on


class ItemSelectModal(ModalScreen[str | None]):
    """
    Custom textual modal displaying a list of selectable items.
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, items: dict, title: str) -> None:
        super().__init__()
        self._items = items
        self._title = title


    def compose(self) -> Generator:
        content = ListView(
            *[
                ListItem(Label(str(self._items.get(i)), classes="ism-item-label"), name=i, classes="ism-item")
                for i in self._items
            ],
            classes="ism-list"
        ) if self._items else Label("No options available", classes="ism-list")
        
        yield Container(
            Label(self._title, classes="ism-title"),
            content
        )


    @on(ListView.Selected)
    def _on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Event handler for when a list item is selected.
        Yields the name of the list item.
        """
        
        self.dismiss(event.item.name)


    def action_cancel(self) -> None:
        """
        Textual action to dismiss this ItemSelectModal without doing anything.
        Bound to the 'escape' key.
        """
        
        self.dismiss(None)
