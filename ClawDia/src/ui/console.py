import shutil
from typing import Optional

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.text import Text
from rich import box

console = RichConsole()


class ConsoleUI:
    def __init__(self):
        self.console = console
        self.width = shutil.get_terminal_size((100, 24)).columns

    def welcome(self, version: str = "0.1.0"):
        title = Text(f"ClawDia v{version}", style="bold cyan")
        subtitle = Text("  Offline AI Assistant", style="dim white")
        panel = Panel(title + "\n" + subtitle, box=box.ROUNDED, border_style="cyan")
        self.console.print(panel)

    def echo(self, text: str, style: str = "white"):
        self.console.print(text, style=style)

    def info(self, text: str):
        self.console.print(f"[dim]╰─[/dim] {text}")

    def success(self, text: str):
        self.console.print(f"[bold green]✓[/bold green] {text}")

    def warning(self, text: str):
        self.console.print(f"[bold yellow]⚠[/bold yellow] {text}")

    def error(self, text: str):
        self.console.print(f"[bold red]✗[/bold red] {text}")

    def panel(self, content: str, title: str = "", style: str = "cyan"):
        panel = Panel(content, title=title, box=box.ROUNDED, border_style=style)
        self.console.print(panel)

    def markdown(self, text: str):
        self.console.print(Markdown(text))

    def code(self, code: str, lang: str = "python"):
        self.console.print(Syntax(code, lang, theme="monokai"))

    def table(self, headers: list, rows: list, title: str = "") -> Table:
        table = Table(title=title, box=box.SIMPLE, border_style="cyan")
        for h in headers:
            table.add_column(h, style="bold")
        for row in rows:
            table.add_row(*[str(c) for c in row])
        self.console.print(table)
        return table

    def prompt_text(self, message: str = "") -> str:
        return Prompt.ask(message)

    def prompt_int(self, message: str = "") -> Optional[int]:
        try:
            return IntPrompt.ask(message)
        except ValueError:
            return None

    def prompt_confirm(self, message: str = "") -> bool:
        return Confirm.ask(message)

    def spinner(self, message: str = "Processing..."):
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        )

    def status(self, message: str):
        return self.console.status(message)

    def divider(self):
        self.console.print("─" * min(self.width, 60), style="dim")
