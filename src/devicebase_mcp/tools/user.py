"""Account tools — the API key's own profile and the daily check-in.

Unprefixed like the other platform-agnostic tools: these address the account
rather than a device, over ``/v1/user/*``, and take no serialno — the key says
who is asking, and it can only ever be the user's own account.

The check-in tool is the one tool here that is deliberately safe to run
unattended: claiming twice in a day is not an error, so the model can put it in
a scheduled task without checking first. Setting that task up is still the
user's call — this tool claims today's points when asked to, it does not decide
on its own to start claiming them every day.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DevicebaseClient
from devicebase_mcp.tools import ToolContext


def register_user_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register the account tools."""

    def emit(result: dict[str, object]) -> str:
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def user_info(ctx: ToolContext | None = None) -> str:
        """Report the account behind the API key: name, phone, points, signup date.

        Use it when the user asks who they are on the platform, what their
        phone number on file is, how many points they have, when they signed
        up, or whether today's check-in is still available (data.can_checkin).

        There is no way to ask about another account: the API key decides whose
        record this is, so this always answers for the user you are working for.

        Returns:
            JSON whose data holds username (the name shown in the console),
            mobile, credits (the points balance), registered_at, and
            can_checkin.
        """
        return emit(client.user_info(context=ctx))

    @mcp.tool()
    def user_checkin(ctx: ToolContext | None = None) -> str:
        """Claim today's points for the account — the daily check-in.

        Call it when the user asks you to check in or to collect their daily
        points. If they ask for this every day, the right answer is a scheduled
        task that runs `devicebase user checkin` (or calls this tool) on their
        machine — offer to set that up rather than checking in on your own
        initiative: the schedule is their decision, and it should be visible
        somewhere they can see and change it.

        Points are granted once a day: 25 on the first day, plus 10 for each
        consecutive day, up to 95 a day. Claiming again the same day is **not**
        an error — data.already_checked comes back true, data.credits_earned is
        0, and data.message says "今日已签到" — so a task that runs this on a
        schedule needs no guard and will not double-claim. Show data.message to
        the user; it is the platform's own wording.

        Returns:
            JSON whose data holds success, credits_earned, consecutive_days,
            already_checked, message and credits (the balance afterwards).
        """
        return emit(client.user_checkin(context=ctx))
