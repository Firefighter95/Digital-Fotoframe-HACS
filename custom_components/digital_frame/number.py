from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity


@dataclass(frozen=True)
class DigitalFrameNumberDescription:
    key: str
    name: str
    config_key: str
    minimum: float
    maximum: float
    step: float
    unit: str | None
    icon: str
    mode: str = "slider"


NUMBERS: tuple[DigitalFrameNumberDescription, ...] = (
    DigitalFrameNumberDescription("slide_seconds", "Slideshow interval", "slideSeconds", 3, 3600, 1, UnitOfTime.SECONDS, "mdi:timer-outline", "box"),
    DigitalFrameNumberDescription("photo_overlay", "Photo dark overlay", "photoOverlay", 0, 85, 1, PERCENTAGE, "mdi:brightness-4"),
    DigitalFrameNumberDescription("clock_size", "Clock size", "clockSize", 70, 160, 1, PERCENTAGE, "mdi:format-size"),
    DigitalFrameNumberDescription("clock_backdrop_opacity", "Clock backdrop opacity", "clockBackdropOpacity", 0, 95, 1, PERCENTAGE, "mdi:opacity"),
    DigitalFrameNumberDescription("page_fallback_seconds", "Page fallback seconds", "pageFallbackSeconds", 5, 300, 5, UnitOfTime.SECONDS, "mdi:timer-alert-outline", "box"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(DigitalFrameNumber(coordinator, description) for description in NUMBERS)


class DigitalFrameNumber(DigitalFrameEntity, NumberEntity):
    def __init__(
        self,
        coordinator: DigitalFrameCoordinator,
        description: DigitalFrameNumberDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum
        self._attr_native_step = description.step
        self._attr_native_unit_of_measurement = description.unit
        self._attr_mode = description.mode

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "settings" in permissions and super().available

    @property
    def native_value(self) -> float | None:
        value: Any = (self.coordinator.data or {}).get("config", {}).get(self.entity_description.config_key)
        if value is None:
            return None
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_call_and_refresh(
            self.coordinator.api.async_update_config(**{self.entity_description.config_key: value})
        )
