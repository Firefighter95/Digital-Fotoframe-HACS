from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity


@dataclass(frozen=True)
class DigitalFrameSwitchDescription:
    key: str
    name: str
    icon: str
    is_on: Callable[[dict[str, Any]], bool]
    turn_on: Callable[[DigitalFrameCoordinator], Awaitable[None]]
    turn_off: Callable[[DigitalFrameCoordinator], Awaitable[None]]
    required_permission: str = "settings"


CONFIG_SWITCHES: tuple[DigitalFrameSwitchDescription, ...] = (
    DigitalFrameSwitchDescription(
        "clock_enabled",
        "Clock",
        "mdi:clock-outline",
        lambda data: data.get("config", {}).get("showClock") is not False,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(showClock=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(showClock=False)),
    ),
    DigitalFrameSwitchDescription(
        "countdown_enabled",
        "Countdown",
        "mdi:timer-outline",
        lambda data: data.get("config", {}).get("countdownEnabled") is True,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(countdownEnabled=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(countdownEnabled=False)),
    ),
    DigitalFrameSwitchDescription(
        "shuffle",
        "Shuffle photos",
        "mdi:shuffle",
        lambda data: data.get("config", {}).get("shuffle") is True,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(shuffle=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(shuffle=False)),
    ),
    DigitalFrameSwitchDescription(
        "clock_backdrop",
        "Clock backdrop",
        "mdi:card-text-outline",
        lambda data: data.get("config", {}).get("clockBackdrop") is not False,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(clockBackdrop=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(clockBackdrop=False)),
    ),
    DigitalFrameSwitchDescription(
        "favorites_only",
        "Favorites only",
        "mdi:star-outline",
        lambda data: data.get("config", {}).get("photoSource") == "favorites",
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_set_photo_source("favorites")),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_set_photo_source("all")),
    ),
    DigitalFrameSwitchDescription(
        "adaptive_readability",
        "Adaptive readability",
        "mdi:theme-light-dark",
        lambda data: data.get("config", {}).get("adaptiveReadability") is not False,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(adaptiveReadability=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(adaptiveReadability=False)),
    ),
    DigitalFrameSwitchDescription(
        "burn_in_protection",
        "Burn-in protection",
        "mdi:monitor-shimmer",
        lambda data: data.get("config", {}).get("burnInProtection") is not False,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(burnInProtection=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(burnInProtection=False)),
    ),
    DigitalFrameSwitchDescription(
        "smooth_transitions",
        "Smooth transitions",
        "mdi:transition",
        lambda data: data.get("config", {}).get("smoothTransitions") is not False,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(smoothTransitions=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(smoothTransitions=False)),
    ),
    DigitalFrameSwitchDescription(
        "smart_day_mode",
        "Smart day mode",
        "mdi:sun-clock-outline",
        lambda data: data.get("config", {}).get("smartMode") is True,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(smartMode=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(smartMode=False)),
    ),
    DigitalFrameSwitchDescription(
        "self_healing",
        "Kiosk self-healing",
        "mdi:auto-fix",
        lambda data: data.get("config", {}).get("selfHealing") is not False,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(selfHealing=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(selfHealing=False)),
    ),
    DigitalFrameSwitchDescription(
        "page_error_fallback",
        "Page error fallback",
        "mdi:backup-restore",
        lambda data: data.get("config", {}).get("fallbackOnPageError") is not False,
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(fallbackOnPageError=True)),
        lambda coordinator: coordinator.async_call_and_refresh(coordinator.api.async_update_config(fallbackOnPageError=False)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [DigitalFrameScreenSwitch(coordinator)]
        + [DigitalFrameConfigSwitch(coordinator, description) for description in CONFIG_SWITCHES]
    )


class DigitalFrameScreenSwitch(DigitalFrameEntity, SwitchEntity):
    _attr_icon = "mdi:monitor"

    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "screen_power", "Screen")

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "display" in permissions and super().available

    @property
    def is_on(self) -> bool:
        return (self.coordinator.data or {}).get("screen", {}).get("power") != "off"

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_set_screen("on"))

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_set_screen("off"))


class DigitalFrameConfigSwitch(DigitalFrameEntity, SwitchEntity):
    def __init__(self, coordinator: DigitalFrameCoordinator, description: DigitalFrameSwitchDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return self.entity_description.required_permission in permissions and super().available

    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on(self.coordinator.data or {})

    async def async_turn_on(self, **kwargs) -> None:
        await self.entity_description.turn_on(self.coordinator)

    async def async_turn_off(self, **kwargs) -> None:
        await self.entity_description.turn_off(self.coordinator)
