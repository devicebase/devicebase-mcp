"""Errors raised by the Devicebase client.

The API reports failures through two layers, and both are surfaced here:

* a non-2xx HTTP status becomes one of the status-specific errors below;
* a business failure carried inside an otherwise successful response — HTTP 200
  with a non-2xx ``code`` in the envelope — becomes :class:`BusinessError`.
"""

from __future__ import annotations


class DevicebaseError(Exception):
    """Base error for the Devicebase client."""


class AuthenticationError(DevicebaseError):
    """The API key is missing, or the server rejected it (HTTP 401)."""


class DeviceNotFoundError(DevicebaseError):
    """The device is not found or not connected (HTTP 404)."""


class ValidationError(DevicebaseError):
    """The server rejected the request parameters."""


class BusinessError(DevicebaseError):
    """The API answered with a success status but failed inside the envelope.

    The control API returns HTTP 200 with a non-2xx ``code`` for action
    failures — a browser selector that matches nothing, a computer command that
    cannot run. Guarding on the HTTP status alone would report those as success.
    """

    def __init__(self, code: int, body: str) -> None:
        super().__init__(f"API error (code {code}): {body}")
        self.code = code
        self.body = body
