#!/usr/bin/env python3

from pythorhead import Lemmy
from pythorhead.types import SearchType, ListingType, SortType

from textual.app import App
from textual.containers import ScrollableContainer
from textual.widgets import Button, Footer, Header, Static, Input, Label, RichLog
from textual.events import Focus
from textual import on


class LoginForm(ScrollableContainer):
    lemmy = None

    def compose(self):
        yield Input(placeholder="Instance URL", id='inst')
        yield Input(placeholder="Username", id='user')
        yield Input(placeholder="Password", password=True, id='passwd')
        yield Label()

    @on(Input.Submitted)
    def go_next(self, event):
        inst = self.query_one("#inst")
        user = self.query_one("#user")
        passwd = self.query_one("#passwd")
        if event.input is inst:
            user.focus()
        elif event.input is user:
            passwd.focus()
        else:
            self.log_in()

    def log_in(self):
        inst = self.query_one("#inst").value
        if not inst.startswith("http"):
            inst = "https://" + inst
        user = self.query_one("#user").value
        passwd = self.query_one("#passwd").value
        label = self.query_one(Label)
        if not (lemmy := Lemmy(inst)).nodeinfo:
            label.update(f"Failed connection to {inst}")
            return
        if not lemmy.log_in(user, passwd):
            label.update(f"Failed login for {user}") 
            return
        self.lemmy = lemmy
        label.update("Success!")


class Post(Static):
    def compose(self):
        yield Static("Cool stuff broo")


class PostView(ScrollableContainer):
    BINDINGS = [
        ("up", "go_up", "Go up"),
        ("down", "go_down", "Go down"),
    ]

    idx = 0

    def on_mount(self) -> None:
        self._move_selection(0)

    def _move_selection(self, direction):
        posts = self.query('Post')
        if not posts:
            return
        posts[self.idx].remove_class('selected')
        self.idx = (self.idx + direction) % len(posts)
        posts[self.idx].add_class('selected')

    def action_go_up(self):
        self._move_selection(-1)

    def action_go_down(self):
        self._move_selection(1)


class LemmyTUI(App):
    CSS_PATH = "lemmy-tui.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    lemmy = None

    def compose(self):
        yield Header()
        yield Footer()
        # yield PostView(id='posts')
        yield LoginForm()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = LemmyTUI()
    app.run()
