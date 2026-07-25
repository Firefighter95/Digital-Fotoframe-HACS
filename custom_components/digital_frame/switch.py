from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
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
    async_add_entities([DigitalFrameScreenSwitch(coordinator)])


class DigitalFrameScreenSwitch(DigitalFrameEntity, SwitchEntity):
    _attr_icon = "mdi:monitor"

    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "screen_power", "Screen")

    @property
    def is_on(self) -> bool:
        return (self.coordinator.data or {}).get("screen", {}).get("power") != "off"

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_set_screen("on"))

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_set_screen("off"))
