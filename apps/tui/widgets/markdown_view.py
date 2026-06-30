import re

from textual.app import ComposeResult
from textual.widgets import Markdown
from textual.containers import Vertical

from widgets.code_block import CodeBlock

# regex to match markdown fenced code blocks
CODE_BLOCK_RE = re.compile(
    r"```(?P<lang>[a-zA-Z0-9_-]+)?\n(?P<code>.*?)```",
    re.DOTALL,
)


class MarkdownView(Vertical):
    """
    Markdown renderer that:
    - uses Textual Markdown for prose
    - uses CodeBlock for fenced code blocks
    """

    def __init__(self, content: str, classes: str = "") -> None:
        super().__init__(classes=classes)
        self.content = content


    def compose(self) -> ComposeResult:
        """
        Textual compose method override.
        Uses custom builder to compose widget.
        """
        
        yield from self._build_widgets()


    def _build_widgets(self) -> ComposeResult:
        """
        Separates markdown fenced code blocks from other markdown prose and builds
        widgets for each separately.
        """
        
        last_index = 0

        for match in CODE_BLOCK_RE.finditer(self.content):
            start, end = match.span()

            # handle normal markdown before code block
            if start > last_index:
                prose = self.content[last_index:start].strip("\n")
                if prose:
                    yield Markdown(prose)

            # handle code block
            lang = match.group("lang") or "text"
            code = match.group("code")

            yield CodeBlock(code, lang)

            last_index = end

        # handle trailing content
        if last_index < len(self.content):
            remaining = self.content[last_index:].strip("\n")
            if remaining:
                yield Markdown(remaining)
            
            
    def update(self, content: str) -> None:
        """
        Custom update method for updating this widget's contents.
        (Expensive!)
        """
        
        self.content = content
        self.remove_children()
        self.mount_all(self._build_widgets())
