from typing import Callable, Optional

from rich.table import Table
from rich import box

from .console import console


class MenuItem:
    def __init__(self, label: str, handler: Callable, key: str = ""):
        self.label = label
        self.handler = handler
        self.key = key or label[0].upper()


class Menu:
    def __init__(self, title: str = "Menu"):
        self.title = title
        self.items: list[MenuItem] = []

    def add(self, label: str, handler: Callable, key: str = ""):
        self.items.append(MenuItem(label, handler, key))

    def show(self) -> Optional[str]:
        table = Table(
            title=self.title,
            box=box.SIMPLE,
            border_style="cyan",
            show_header=False,
            padding=(0, 2),
        )
        table.add_column("Key", style="bold yellow", width=4)
        table.add_column("Action", style="white")
        for item in self.items:
            table.add_row(f"[{item.key}]", item.label)
        console.print(table)

        while True:
            choice = console.input("\n[bold cyan]?[/bold cyan] ").strip().upper()
            if choice == "Q":
                return None
            for item in self.items:
                if choice == item.key:
                    return item.handler(item)
            console.print(f"[red]Invalid: {choice}[/red]")
