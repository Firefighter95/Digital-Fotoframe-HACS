from __future__ import annotations

from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DigitalFrameUpdate(coordinator)])


class DigitalFrameUpdate(DigitalFrameEntity, UpdateEntity):
    _attr_icon = "mdi:package-up"
    _attr_supported_features = UpdateEntityFeature.INSTALL
    _attr_title = "Digital Frame"

    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "software_update", "Software update")

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "updates" in permissions and super().available

    @property
    def installed_version(self) -> str | None:
        return (self.coordinator.data or {}).get("server", {}).get("appVersion")

    @property
    def latest_version(self) -> str | None:
        update = (self.coordinator.data or {}).get("update", {})
        if update.get("status") in ("ready", "failed"):
            return update.get("packageName") or "Uploaded update package"
        return self.installed_version

    @property
    def in_progress(self) -> bool:
        return (self.coordinator.data or {}).get("update", {}).get("status") == "applying"

    @property
    def release_summary(self) -> str | None:
        update = (self.coordinator.data or {}).get("update", {})
        if update.get("status") in ("ready", "failed"):
            return f"Uploaded by {update.get('uploadedBy') or 'unknown'} at {update.get('uploadedAt') or 'unknown'}."
        if update.get("lastError"):
            return str(update["lastError"])[:255]
        return None

    def version_is_newer(self, latest_version: str, installed_version: str) -> bool:
        return (self.coordinator.data or {}).get("update", {}).get("status") in ("ready", "failed")

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_apply_update())
