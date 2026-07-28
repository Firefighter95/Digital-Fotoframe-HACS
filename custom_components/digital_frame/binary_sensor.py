from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity


def _system(data: dict[str, Any]) -> dict[str, Any]:
    system = data.get("systemInfo")
    return system if isinstance(system, dict) else {}


def _browser(data: dict[str, Any]) -> dict[str, Any]:
    browser = _system(data).get("browser")
    return browser if isinstance(browser, dict) else {}


def _display(data: dict[str, Any]) -> dict[str, Any]:
    display = data.get("display")
    return display if isinstance(display, dict) else {}


def _has_problem(data: dict[str, Any]) -> bool:
    return any(
        bool(value)
        for value in (
            _display(data).get("lastControlError"),
            data.get("screen", {}).get("lastError"),
            data.get("browser", {}).get("lastError"),
            _browser(data).get("lastError"),
            data.get("update", {}).get("lastError"),
            data.get("smart", {}).get("lastProblem"),
            data.get("systemInfoError"),
        )
    )


@dataclass(frozen=True)
class DigitalFrameBinarySensorDescription:
    key: str
    name: str
    value_fn: Callable[[dict[str, Any]], bool | None]
    icon: str
    device_class: BinarySensorDeviceClass | None = None
    requires_system: bool = False


BINARY_SENSORS: tuple[DigitalFrameBinarySensorDescription, ...] = (
    DigitalFrameBinarySensorDescription(
        "display_connected",
        "Display connected",
        lambda data: _display(data).get("connected") is True,
        "mdi:monitor-eye",
        BinarySensorDeviceClass.CONNECTIVITY,
    ),
    DigitalFrameBinarySensorDescription(
        "kiosk_browser_connected",
        "Kiosk browser connected",
        lambda data: _browser(data).get("devtoolsAvailable") is True,
        "mdi:web-check",
        BinarySensorDeviceClass.CONNECTIVITY,
        requires_system=True,
    ),
    DigitalFrameBinarySensorDescription(
        "browser_fullscreen",
        "Browser fullscreen",
        lambda data: _browser(data).get("fullscreen"),
        "mdi:fullscreen",
        BinarySensorDeviceClass.RUNNING,
        requires_system=True,
    ),
    DigitalFrameBinarySensorDescription(
        "problem",
        "Problem",
        _has_problem,
        "mdi:alert-circle-outline",
        BinarySensorDeviceClass.PROBLEM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(DigitalFrameBinarySensor(coordinator, description) for description in BINARY_SENSORS)


class DigitalFrameBinarySensor(DigitalFrameEntity, BinarySensorEntity):
    def __init__(
        self,
        coordinator: DigitalFrameCoordinator,
        description: DigitalFrameBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class

    @property
    def available(self) -> bool:
        if self.entity_description.requires_system and not _system(self.coordinator.data or {}):
            return False
        return super().available

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data or {})
