from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import DigitalFrameApi
from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity


@dataclass(frozen=True)
class DigitalFrameButtonDescription:
    key: str
    name: str
    icon: str
    method: Callable[[DigitalFrameApi], Awaitable[dict[str, Any]]]
    required_permission: str = "display"
    device_class: ButtonDeviceClass | None = None


BUTTONS: tuple[DigitalFrameButtonDescription, ...] = (
    DigitalFrameButtonDescription(
        "reload_display",
        "Reload display",
        "mdi:reload",
        lambda api: api.async_display_control("reload"),
    ),
    DigitalFrameButtonDescription(
        "force_fullscreen",
        "Force fullscreen",
        "mdi:fullscreen",
        lambda api: api.async_display_control("force_fullscreen"),
    ),
    DigitalFrameButtonDescription(
        "next_photo",
        "Next photo",
        "mdi:skip-next",
        lambda api: api.async_display_control("next_photo"),
    ),
    DigitalFrameButtonDescription(
        "previous_photo",
        "Previous photo",
        "mdi:skip-previous",
        lambda api: api.async_display_control("previous_photo"),
    ),
    DigitalFrameButtonDescription(
        "identify",
        "Identify",
        "mdi:crosshairs-gps",
        lambda api: api.async_display_control("identify"),
        device_class=ButtonDeviceClass.IDENTIFY,
    ),
    DigitalFrameButtonDescription(
        "restart_kiosk",
        "Restart kiosk browser",
        "mdi:web-refresh",
        lambda api: api.async_display_control("restart_kiosk"),
        device_class=ButtonDeviceClass.RESTART,
    ),
    DigitalFrameButtonDescription(
        "restart_pc",
        "Restart PC",
        "mdi:restart",
        lambda api: api.async_system_power("restart"),
        required_permission="system",
        device_class=ButtonDeviceClass.RESTART,
    ),
    DigitalFrameButtonDescription(
        "shutdown_pc",
        "Shut down PC",
        "mdi:power",
        lambda api: api.async_system_power("shutdown"),
        required_permission="system",
    ),
    DigitalFrameButtonDescription(
        "cancel_shutdown",
        "Cancel shutdown",
        "mdi:cancel",
        lambda api: api.async_system_power("cancel"),
        required_permission="system",
    ),
    DigitalFrameButtonDescription(
        "apply_update",
        "Apply uploaded update",
        "mdi:package-up",
        lambda api: api.async_apply_update(),
        required_permission="updates",
        device_class=ButtonDeviceClass.UPDATE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(DigitalFrameButton(coordinator, description) for description in BUTTONS)


class DigitalFrameButton(DigitalFrameEntity, ButtonEntity):
    def __init__(
        self,
        coordinator: DigitalFrameCoordinator,
        description: DigitalFrameButtonDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        if self.entity_description.required_permission not in permissions:
            return False
        if self.entity_description.key == "apply_update":
            update = (self.coordinator.data or {}).get("update", {})
            return super().available and update.get("status") in ("ready", "failed", "missing")
        return super().available

    async def async_press(self) -> None:
        await self.coordinator.async_call_and_refresh(self.entity_description.method(self.coordinator.api))
