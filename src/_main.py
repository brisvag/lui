#!/usr/bin/env python3

import contextlib
import os
from typing import ClassVar

from pythorhead import Lemmy
from pythorhead.types import ListingType, SearchType, SortType
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, Select, Static

# log = RichLog()


class LoginForm(ScrollableContainer):
    def compose(self) -> ComposeResult:
        inst = os.environ.get("LUI_INSTANCE", "")
        user = os.environ.get("LUI_USERNAME", "")
        passwd = os.environ.get("LUI_PASSWORD", "")
        yield Input(inst, placeholder="Instance URL", id="inst")
        yield Input(user, placeholder="Username", id="user")
        yield Input(passwd, placeholder="Password", password=True, id="passwd")
        yield Label()

    @on(Input.Submitted)
    def go_next(self, event: Input.Submitted) -> None:
        inst = self.query_one("#inst")
        user = self.query_one("#user")
        passwd = self.query_one("#passwd")
        if event.input is inst:
            user.focus()
        elif event.input is user:
            passwd.focus()
        else:
            self.log_in()

    def log_in(self) -> None:
        inst = self.query_one("#inst", Input).value
        if not inst.startswith("http"):
            inst = "https://" + inst
        inst.strip("/")
        user = self.query_one("#user", Input).value
        passwd = self.query_one("#passwd", Input).value
        label = self.query_one(Label)
        if not (lemmy := Lemmy(inst)).nodeinfo:
            label.update(f"Failed connection to {inst}")
            return
        if user and passwd:
            if not lemmy.log_in(user, passwd):
                label.update(f"Failed login for {user}")
                return

        label.update("Success!")
        self.parent.parent.add_class("logged")
        self.parent.parent.connect_lemmy_view(lemmy)


class Post(Static):
    focusable = True


class PostView(ScrollableContainer):
    BINDINGS: ClassVar = [
        ("up,k", "go_up", "Go up"),
        ("down,j", "go_down", "Go down"),
    ]

    def add_post(self, post: dict) -> None:
        self.mount(Post(post["post"]["name"]))


class Search(Static):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search...", id="query")
        yield Select(
            [(e.value, e.value) for e in SearchType],
            value=SearchType.Posts,
            allow_blank=False,
            prompt="Type",
            classes="dropdown",
            id="searchtype",
        )
        yield Select(
            [(e.value, e.value) for e in SortType],
            value=SortType.Active,
            allow_blank=False,
            prompt="Sorting",
            classes="dropdown",
            id="sorttype",
        )
        yield Select(
            [(e.value, e.value) for e in ListingType],
            value=ListingType.Subscribed,
            allow_blank=False,
            prompt="Listing",
            classes="dropdown",
            id="listingtype",
        )


class LemmyView(Static):
    lemmy: Lemmy | None = reactive(None)

    def watch_lemmy(self, old: Lemmy | None, lemmy: Lemmy) -> None:
        if lemmy is None or (old is not None and lemmy.nodeinfo == old.nodeinfo):
            return

        self.action_search()

    def compose(self) -> ComposeResult:
        yield Search(id="search")
        yield PostView(id="posts")

    @on(Input.Submitted)
    def on_search(self, event: Input.Submitted) -> None:
        self.action_search()

    def action_search(self) -> None:
        if self.lemmy is None:
            return

        search = self.query_one("#search", Search)

        result = self.lemmy.search(
            q=search.query_one("#query", Input).value,
            type_=search.query_one("#searchtype", Select).value,
            sort=search.query_one("#sorttype", Select).value,
            listing_type=search.query_one("#listingtype", Select).value,
            limit=20,
        )
        postview = self.query_one(PostView)
        postview.remove_children()
        search.remove_class("searching")
        for post in result["posts"]:
            postview.add_post(post)
        if result["posts"]:
            postview.query(Post)[0].focus()


class LemmyUIApp(App):
    CSS_PATH = "lui.css"
    BINDINGS: ClassVar = [
        Binding("escape", "focus_parent", "Focus parent"),
        Binding("h", "focus_parent", "Focus parent"),
        Binding("enter,l", "focus_child", "Focus child"),
        Binding("/", "start_search", "Start search"),
        Binding("up,k", "focus_previous", "Focus previous widget"),
        Binding("down,j", "focus_next", "Focus next widget"),
        Binding("ctrl+l", "log_in", "Log in"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield LoginForm(id="login")
        yield LemmyView(id="lemmyview")
        yield Footer()

    def connect_lemmy_view(self, lemmy: Lemmy) -> None:
        self.query_one(LemmyView).lemmy = lemmy

    def action_focus_parent(self) -> None:
        try:
            self.parent.focus()
        except AttributeError:
            self.action_focus_previous()

    # def on_key(self, event: Key) -> None:
    #     log.write(self)
    #     log.write(event)

    def action_start_search(self) -> None:
        with contextlib.suppress(NoMatches):
            search = self.query_one("#search")
            search.add_class("searching")
            search.query_one("#query").focus()

    def action_log_in(self) -> None:
        self.remove_class("logged")


if __name__ == "__main__":
    app = LemmyUIApp()
    app.run()
