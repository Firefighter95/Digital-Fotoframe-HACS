from __future__ import annotations

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity

DEFAULT_NOTIFY_DURATION = 60
DEFAULT_NOTIFY_ACCENT = "#d5a849"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DigitalFrameNotify(coordinator)])


class DigitalFrameNotify(DigitalFrameEntity, NotifyEntity):
    _attr_icon = "mdi:message-alert-outline"

    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "notify", "Notify")

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "display" in permissions and super().available

    async def async_send_message(self, message: str, title: str | None = None, **kwargs) -> None:
        data = kwargs.get("data") if isinstance(kwargs.get("data"), dict) else {}
        await self.coordinator.async_call_and_refresh(
            self.coordinator.api.async_show_message(
                title or "Home Assistant",
                message,
                int(data.get("duration", DEFAULT_NOTIFY_DURATION)),
                str(data.get("accent", DEFAULT_NOTIFY_ACCENT)),
            )
        )
        self._async_record_notification()
