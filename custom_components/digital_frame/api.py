from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

from aiohttp import ClientError, ClientSession


class DigitalFrameError(Exception):
    """Base error for the Digital Frame API."""


class DigitalFrameCannotConnect(DigitalFrameError):
    """Raised when the frame cannot be reached."""


class DigitalFrameAuthError(DigitalFrameError):
    """Raised when the configured PIN is not accepted."""


class DigitalFrameApi:
    def __init__(self, session: ClientSession, host: str, port: int, pin: str, actor: str) -> None:
        self._session = session
        parsed = urlparse(host.strip() if "://" in host else f"http://{host.strip()}")
        self.host = parsed.hostname or host.strip().split("/")[0].split(":")[0]
        self.port = int(parsed.port or port)
        self.pin = pin
        self.actor = actor

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    async def _request(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {
            "x-frame-pin": self.pin,
            "x-frame-actor": self.actor,
        }
        body = json
        if body is not None:
            body = {"pin": self.pin, "actor": self.actor, **body}
        try:
            async with asyncio.timeout(8):
                response = await self._session.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=headers,
                    json=body,
                )
                data = await response.json(content_type=None)
        except (asyncio.TimeoutError, ClientError, OSError) as err:
            raise DigitalFrameCannotConnect from err
        except ValueError as err:
            raise DigitalFrameCannotConnect from err

        if response.status in (401, 403):
            raise DigitalFrameAuthError(data.get("error", "PIN niet geaccepteerd."))
        if response.status >= 400:
            raise DigitalFrameError(data.get("error", f"HTTP {response.status}"))
        return data

    async def async_get_state(self) -> dict[str, Any]:
        return await self._request("GET", "/api/state")

    async def async_set_screen(self, action: str) -> dict[str, Any]:
        return await self._request("POST", "/api/screen", json={"action": action})

    async def async_set_mode(self, mode: str) -> dict[str, Any]:
        return await self._request("POST", "/api/command", json={"mode": mode})

    async def async_update_config(self, **config: Any) -> dict[str, Any]:
        return await self._request("POST", "/api/config", json=config)

    async def async_set_photo_source(self, source: str) -> dict[str, Any]:
        return await self.async_update_config(photoSource=source)

    async def async_show_url(self, url: str) -> dict[str, Any]:
        return await self._request("POST", "/api/command", json={"mode": "iframe", "iframe": {"url": url}})

    async def async_show_page(self, page_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/pages/{page_id}/show", json={})

    async def async_show_mode_item(self, item_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/mode-items/{item_id}/show", json={})

    async def async_save_page(self, name: str, url: str, page_id: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name, "url": url}
        if page_id:
            body["id"] = page_id
        return await self._request("POST", "/api/pages", json=body)

    async def async_delete_page(self, page_id: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/api/pages/{page_id}", json={})

    async def async_get_system_info(self) -> dict[str, Any]:
        return await self._request("GET", "/api/system/info")

    async def async_system_power(self, action: str) -> dict[str, Any]:
        return await self._request("POST", "/api/system/power", json={"action": action})

    async def async_display_control(self, action: str) -> dict[str, Any]:
        return await self._request("POST", "/api/display/control", json={"action": action})

    async def async_apply_update(self) -> dict[str, Any]:
        return await self._request("POST", "/api/apply-update", json={})

    async def async_update_weather(self, weather: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/weather", json={"weather": weather})

    async def async_show_message(
        self,
        title: str,
        message: str,
        duration: int = 60,
        accent: str = "#d5a849",
        priority: str = "normal",
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/command",
            json={
                "mode": "message",
                "durationSeconds": duration,
                "message": {
                    "title": title,
                    "body": message,
                    "accent": accent,
                    "priority": priority,
                },
            },
        )
