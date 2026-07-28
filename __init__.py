from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class DigitalFrameConfigTextDescription:
    key: str
    name: str
    config_key: str
    icon: str


CONFIG_TEXTS: tuple[DigitalFrameConfigTextDescription, ...] = (
    DigitalFrameConfigTextDescription("smart_morning_start", "Smart morning start", "smartMorningStart", "mdi:weather-sunset-up"),
    DigitalFrameConfigTextDescription("smart_day_start", "Smart day start", "smartDayStart", "mdi:white-balance-sunny"),
    DigitalFrameConfigTextDescription("smart_evening_start", "Smart evening start", "smartEveningStart", "mdi:weather-sunset-down"),
    DigitalFrameConfigTextDescription("smart_night_start", "Smart night start", "smartNightStart", "mdi:weather-night"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [DigitalFrameMessageText(coordinator)]
        + [DigitalFrameConfigText(coordinator, description) for description in CONFIG_TEXTS]
    )


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
                    "normal",
                )
            )
        except DigitalFrameError as err:
            self._native_value = previous_value
            self.async_write_ha_state()
            raise HomeAssistantError(str(err)) from err


class DigitalFrameConfigText(DigitalFrameEntity, TextEntity):
    def __init__(
        self,
        coordinator: DigitalFrameCoordinator,
        description: DigitalFrameConfigTextDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "settings" in permissions and super().available

    @property
    def mode(self) -> str:
        return "text"

    @property
    def native_min(self) -> int:
        return 5

    @property
    def native_max(self) -> int:
        return 5

    @property
    def native_value(self) -> str | None:
        return (self.coordinator.data or {}).get("config", {}).get(self.entity_description.config_key)

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_call_and_refresh(
            self.coordinator.api.async_update_config(**{self.entity_description.config_key: value.strip()})
        )
