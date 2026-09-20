"""Browser platform tools — Chrome / Chromium / Edge over CDP.

Every tool targets ``/api/browser/{serialno}/{action...}``. Selectors are CSS
selectors. The serialno is a browser device's, from
``list_devices(type="browser")``.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DevicebaseClient
from devicebase_mcp.tools import ToolContext


def register_browser_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register the browser platform tools."""

    def emit(result: dict[str, Any]) -> str:
        return json.dumps(result, ensure_ascii=False)

    # --- Navigation ---

    @mcp.tool()
    def browser_navigate(serialno: str, url: str, ctx: ToolContext | None = None) -> str:
        """Navigate the current tab to a URL.

        Args:
            serialno: The browser device serialno, from list_devices.
            url: The destination URL.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_navigate(serialno, url, context=ctx))

    @mcp.tool()
    def browser_refresh(serialno: str, ctx: ToolContext | None = None) -> str:
        """Reload the current page.

        Args:
            serialno: The browser device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_refresh(serialno, context=ctx))

    @mcp.tool()
    def browser_go_back(serialno: str, ctx: ToolContext | None = None) -> str:
        """Navigate back in the browser history.

        Args:
            serialno: The browser device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_go_back(serialno, context=ctx))

    @mcp.tool()
    def browser_go_forward(serialno: str, ctx: ToolContext | None = None) -> str:
        """Navigate forward in the browser history.

        Args:
            serialno: The browser device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_go_forward(serialno, context=ctx))

    # --- DOM ---

    @mcp.tool()
    def browser_click(serialno: str, selector: str, ctx: ToolContext | None = None) -> str:
        """Click the element matching a CSS selector.

        Args:
            serialno: The browser device serialno, from list_devices.
            selector: A CSS selector.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_click(serialno, selector, context=ctx))

    @mcp.tool()
    def browser_fill(
        serialno: str, selector: str, value: str, ctx: ToolContext | None = None
    ) -> str:
        """Clear an input and type a value into it.

        Args:
            serialno: The browser device serialno, from list_devices.
            selector: A CSS selector for the input.
            value: The value to type.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_fill(serialno, selector, value, context=ctx))

    @mcp.tool()
    def browser_select(
        serialno: str, selector: str, value: str, ctx: ToolContext | None = None
    ) -> str:
        """Pick an option in a dropdown.

        Args:
            serialno: The browser device serialno, from list_devices.
            selector: A CSS selector for the select element.
            value: The option value to select.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_select(serialno, selector, value, context=ctx))

    @mcp.tool()
    def browser_text(serialno: str, selector: str, ctx: ToolContext | None = None) -> str:
        """Get an element's text content.

        Args:
            serialno: The browser device serialno, from list_devices.
            selector: A CSS selector.

        Returns:
            JSON envelope whose data carries the text.
        """
        return emit(client.browser_text(serialno, selector, context=ctx))

    @mcp.tool()
    def browser_attribute(
        serialno: str, selector: str, attribute: str, ctx: ToolContext | None = None
    ) -> str:
        """Get one attribute of an element.

        Args:
            serialno: The browser device serialno, from list_devices.
            selector: A CSS selector.
            attribute: The attribute name, e.g. href.

        Returns:
            JSON envelope whose data carries the attribute value.
        """
        return emit(client.browser_attribute(serialno, selector, attribute, context=ctx))

    @mcp.tool()
    def browser_exists(serialno: str, selector: str, ctx: ToolContext | None = None) -> str:
        """Check whether an element is present.

        Args:
            serialno: The browser device serialno, from list_devices.
            selector: A CSS selector.

        Returns:
            JSON envelope whose data reports existence.
        """
        return emit(client.browser_exists(serialno, selector, context=ctx))

    @mcp.tool()
    def browser_execute(serialno: str, script: str, ctx: ToolContext | None = None) -> str:
        """Evaluate JavaScript in the page.

        Danger tier: the script runs with the page's own privileges, the same
        reach as shell access to the browser profile.

        Args:
            serialno: The browser device serialno, from list_devices.
            script: The JavaScript source to evaluate.

        Returns:
            JSON envelope whose data carries the script result.
        """
        return emit(client.browser_execute(serialno, script, context=ctx))

    @mcp.tool()
    def browser_input(serialno: str, text: str, ctx: ToolContext | None = None) -> str:
        """Insert text into the focused page element.

        Uses CDP Input.insertText, which is reliable for CJK unlike synthesised
        key events.

        Args:
            serialno: The browser device serialno, from list_devices.
            text: The text to insert.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_input(serialno, text, context=ctx))

    @mcp.tool()
    def browser_hotkey(serialno: str, keys: list[str], ctx: ToolContext | None = None) -> str:
        """Press keys together, e.g. ["Meta", "a"] to select all.

        Editing shortcuts (select-all, cut, copy, undo, redo) act on the page.
        Browser-chrome shortcuts such as Control+t are not reachable — CDP
        drives the page, not the browser UI.

        Args:
            serialno: The browser device serialno, from list_devices.
            keys: The keys to press together.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_hotkey(serialno, keys, context=ctx))

    # --- Tabs and state ---

    @mcp.tool()
    def browser_state(serialno: str, ctx: ToolContext | None = None) -> str:
        """Get the current URL, title, viewport and tab count.

        Args:
            serialno: The browser device serialno, from list_devices.

        Returns:
            JSON envelope whose data carries the browser state.
        """
        return emit(client.browser_state(serialno, context=ctx))

    @mcp.tool()
    def browser_tabs(serialno: str, ctx: ToolContext | None = None) -> str:
        """List the open tabs.

        Args:
            serialno: The browser device serialno, from list_devices.

        Returns:
            JSON envelope whose data carries the tabs, including their ids.
        """
        return emit(client.browser_tabs(serialno, context=ctx))

    @mcp.tool()
    def browser_tab_open(serialno: str, url: str, ctx: ToolContext | None = None) -> str:
        """Open a new tab at a URL.

        Args:
            serialno: The browser device serialno, from list_devices.
            url: The URL to open.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_tab_open(serialno, url, context=ctx))

    @mcp.tool()
    def browser_tab_close(serialno: str, tab_id: str, ctx: ToolContext | None = None) -> str:
        """Close one tab.

        Args:
            serialno: The browser device serialno, from list_devices.
            tab_id: The tab id, from browser_tabs.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_tab_close(serialno, tab_id, context=ctx))

    @mcp.tool()
    def browser_tab_close_all(serialno: str, ctx: ToolContext | None = None) -> str:
        """Close every tab.

        Args:
            serialno: The browser device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_tab_close_all(serialno, context=ctx))

    @mcp.tool()
    def browser_tab_switch(serialno: str, tab_id: str, ctx: ToolContext | None = None) -> str:
        """Focus one tab.

        Args:
            serialno: The browser device serialno, from list_devices.
            tab_id: The tab id, from browser_tabs.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_tab_switch(serialno, tab_id, context=ctx))

    # --- Lifecycle ---

    @mcp.tool()
    def browser_launch(serialno: str, ctx: ToolContext | None = None) -> str:
        """Start the browser / CDP endpoint.

        Args:
            serialno: The browser device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_launch(serialno, context=ctx))

    @mcp.tool()
    def browser_close(serialno: str, ctx: ToolContext | None = None) -> str:
        """Stop the browser / CDP endpoint.

        Args:
            serialno: The browser device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return emit(client.browser_close(serialno, context=ctx))
