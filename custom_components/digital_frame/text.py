from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import DigitalFrameError
from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity

DEFAULT_MESSAGE_TITLE = "Home Assistant"
DEFAULT_MESSAGE_DURATION = 60
DEFAULT_MESSAGE_ACCENT = "#d5a849"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DigitalFrameMessageText(coordinator)])


class DigitalFrameMessageText(DigitalFrameEntity, TextEntity):
    _attr_icon = "mdi:message-text-outline"

    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "message_text", "Send message")
        self._native_value = ""

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "display" in permissions and super().available

    @property
    def mode(self) -> str:
        return "text"

    @property
    def native_min(self) -> int:
        return 0

    @property
    def native_max(self) -> int:
        return 500

    @property
    def native_value(self) -> str:
        return self._native_value

    async def async_set_value(self, value: str) -> None:
        message = value.strip()
        previous_value = self._native_value
        self._native_value = value
        self.async_write_ha_state()
        if not message:
            return

        try:
            await self.coordinator.async_call_and_refresh(
                self.coordinator.api.async_show_message(
                    DEFAULT_MESSAGE_TITLE,
                    message,
                    DEFAULT_MESSAGE_DURATION,
                    DEFAULT_MESSAGE_ACCENT,
                )
            )
        except DigitalFrameError as err:
            self._native_value = previous_value
            self.async_write_ha_state()
            raise HomeAssistantError(str(err)) from err
