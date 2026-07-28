from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity
from .formatting import format_timestamp


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DigitalFrameStatusImage(coordinator)])


class DigitalFrameStatusImage(DigitalFrameEntity, ImageEntity):
    _attr_content_type = "image/svg+xml"
    _attr_icon = "mdi:image-frame"

    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "status_image", "Status image")

    @property
    def image_last_updated(self) -> datetime | None:
        data = self.coordinator.data or {}
        candidates = (
            data.get("display", {}).get("lastSeenAt"),
            data.get("browser", {}).get("lastLaunchAt"),
            data.get("message", {}).get("updatedAt"),
            data.get("iframe", {}).get("updatedAt"),
            data.get("dashboard", {}).get("updatedAt"),
        )
        for value in candidates:
            if not value:
                continue
            try:
                return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                continue
        return None

    async def async_image(self) -> bytes | None:
        data = self.coordinator.data or {}
        config = data.get("config", {})
        display = data.get("display", {})
        browser = (data.get("systemInfo") or {}).get("browser") or {}
        mode = config.get("mode") or "unknown"
        device = config.get("deviceName") or self.coordinator.config_entry.title
        current = display.get("currentPhotoName") or data.get("iframe", {}).get("pageName") or browser.get("activeUrl") or ""
        fullscreen = "yes" if browser.get("fullscreen") or display.get("fullscreen") else "no"
        connected = "online" if display.get("connected") else "unknown"
        url = browser.get("activeUrl") or data.get("browser", {}).get("lastUrl") or ""
        last_seen = format_timestamp(display.get("lastSeenAt")) or ""

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#111310"/>
  <rect x="52" y="52" width="1176" height="616" rx="22" fill="#1b1e19" stroke="#3f4a3f" stroke-width="2"/>
  <text x="88" y="128" fill="#f4efe4" font-family="Arial, sans-serif" font-size="54" font-weight="700">{escape(str(device))}</text>
  <text x="88" y="204" fill="#a9b7a9" font-family="Arial, sans-serif" font-size="30">Mode: {escape(str(mode))}</text>
  <text x="88" y="266" fill="#f4efe4" font-family="Arial, sans-serif" font-size="38">{escape(str(current))}</text>
  <text x="88" y="354" fill="#a9b7a9" font-family="Arial, sans-serif" font-size="28">Display: {escape(connected)} | Fullscreen: {escape(fullscreen)}</text>
  <text x="88" y="414" fill="#a9b7a9" font-family="Arial, sans-serif" font-size="28">Last seen: {escape(str(last_seen))}</text>
  <text x="88" y="474" fill="#7f8d7f" font-family="Arial, sans-serif" font-size="24">{escape(str(url))}</text>
</svg>"""
        return svg.encode("utf-8")
