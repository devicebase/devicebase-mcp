"""Cloud browser lifecycle tools.

Unprefixed like the other platform-agnostic tools: these build and destroy a
browser the platform runs for you, over ``/v1/browser/*``, and address no
existing device.

The create and delete tools both tell the model to get the user's agreement
first. That is not ceremony — creating one consumes a quota slot the user's
account pays for, and deleting one destroys a browser profile for good, with no
undo. An agent that quietly provisions a browser (or, worse, tidies one away)
has made a decision that belonged to the person it is working for.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DevicebaseClient
from devicebase_mcp.tools import ToolContext


def register_cloud_browser_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register the cloud browser lifecycle tools."""

    def emit(result: dict[str, object]) -> str:
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def cloud_browser_quota(ctx: ToolContext | None = None) -> str:
        """Report how many cloud browsers this account may still create.

        Worth asking before creating one: the answer comes from the same source
        as the check creation performs, so a refusal here means a refusal there.
        Only cloud browsers count — devices attached by hand are not part of the
        allowance.

        Returns:
            JSON whose data holds limit, used and remaining.
        """
        return emit(client.cloud_browser_quota(context=ctx))

    @mcp.tool()
    def create_cloud_browser(
        name: str | None = None,
        window_size: str | None = None,
        wait_seconds: int | None = None,
        ctx: ToolContext | None = None,
    ) -> str:
        """Create a cloud browser on the platform's cluster.

        Ask the user before calling this. It spends one of their quota slots and
        the platform provisions a real machine for it — do not create one
        speculatively, and do not create one because you happened to find no
        device to work with. When there is nothing suitable to use, say so and
        offer to create one; wait for a yes.

        Creation is asynchronous — the browser has to start and register itself
        — so this waits for that (15 seconds by default) and the answer carries
        the `serialno` every other browser tool takes. You do not need to poll
        after it.

        If it has not come up within the wait the call still succeeded:
        `registered` is false and `serialno` is null, with a `device_sn` that
        cloud_browser_status and delete_cloud_browser both accept. That is not a
        failure — a slow start is normal — so do not create a second browser
        because the first was slow.

        A cloud browser always runs headless: it lives on a machine nobody is
        looking at. There is no option for that.

        Args:
            name: Display name for the browser, at most 100 characters.
            window_size: Window size as "1366x768" (width x height).
            wait_seconds: How long to wait for it to register, 0-60. 0 answers
                immediately, which suits creating several at once. Omitted, the
                platform waits its own default of 15.

        Returns:
            JSON whose data holds serialno (the platform key, null until it is
            up), device_sn, name, alias_name and registered. `name` is the
            platform's own identity for the machine; **`alias_name` is the name
            the user gave**, verbatim — show that one.
        """
        return emit(
            client.create_cloud_browser(
                name=name, window_size=window_size, wait_seconds=wait_seconds, context=ctx
            )
        )

    @mcp.tool()
    def cloud_browser_status(identifier: str, ctx: ToolContext | None = None) -> str:
        """Check whether a created cloud browser has come up yet.

        The device row only exists once the node has registered the browser, so
        this is how the wait after create_cloud_browser is spent. "Not up yet"
        is a normal answer — data.registered is false and nothing fails — so
        polling this is quiet.

        Args:
            identifier: The `device_sn` returned by create_cloud_browser, or the
                serialno once the browser is up. Either resolves.

        Returns:
            JSON whose data holds `registered`, and once it is true also
            serialno (what the other tools take), name, state and server_url.
        """
        return emit(client.cloud_browser_status(identifier, context=ctx))

    @mcp.tool()
    def delete_cloud_browser(identifier: str, ctx: ToolContext | None = None) -> str:
        """Delete a cloud browser, irreversibly.

        Ask the user before calling this. The browser and its profile are gone
        for good, and there is no undo — "I am done with it" is the user's
        judgement to make, not yours. This is also not the same as closing a
        browser: it destroys it rather than stopping its engine.

        Only cloud browsers can be deleted here; one attached by hand is not the
        platform's to remove. The call does not wait for the machine — the reap
        is queued and collected on the node's next heartbeat — so it succeeds
        even while the node is offline.

        Args:
            identifier: The platform serialno, or the `device_sn` from creation.

        Returns:
            JSON envelope; data is null on success.
        """
        return emit(client.delete_cloud_browser(identifier, context=ctx))
