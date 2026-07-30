from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity
from .formatting import format_duration, format_timestamp


def _config(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("config", {})


def _screen(data: dict[str, Any]) -> str:
    return data.get("screen", {}).get("power", "unknown")


def _active_page(data: dict[str, Any]) -> str:
    iframe = data.get("iframe", {})
    return iframe.get("pageName") or iframe.get("pageId") or iframe.get("url") or ""


def _system(data: dict[str, Any]) -> dict[str, Any]:
    system = data.get("systemInfo")
    return system if isinstance(system, dict) else {}


def _cpu(data: dict[str, Any]) -> dict[str, Any]:
    cpu = _system(data).get("cpu")
    return cpu if isinstance(cpu, dict) else {}


def _memory(data: dict[str, Any]) -> dict[str, Any]:
    memory = _system(data).get("memory")
    return memory if isinstance(memory, dict) else {}


def _process(data: dict[str, Any]) -> dict[str, Any]:
    process = _system(data).get("process")
    return process if isinstance(process, dict) else {}


def _process_memory(data: dict[str, Any]) -> dict[str, Any]:
    memory = _process(data).get("memory")
    return memory if isinstance(memory, dict) else {}


def _browser(data: dict[str, Any]) -> dict[str, Any]:
    browser = _system(data).get("browser")
    return browser if isinstance(browser, dict) else {}


def _display(data: dict[str, Any]) -> dict[str, Any]:
    display = data.get("display")
    return display if isinstance(display, dict) else {}


def _update(data: dict[str, Any]) -> dict[str, Any]:
    update = data.get("update")
    return update if isinstance(update, dict) else {}


def _smart(data: dict[str, Any]) -> dict[str, Any]:
    smart = data.get("smart")
    return smart if isinstance(smart, dict) else {}


def _first_drive(data: dict[str, Any]) -> dict[str, Any]:
    disk = _system(data).get("disk")
    drives = disk.get("drives") if isinstance(disk, dict) else []
    if isinstance(drives, list) and drives:
        drive = drives[0]
        return drive if isinstance(drive, dict) else {}
    return {}


def _disk_used_percent(data: dict[str, Any]) -> float | None:
    drive = _first_drive(data)
    size = float(drive.get("size") or 0)
    free = float(drive.get("free") or 0)
    if size <= 0:
        return None
    return round(((size - free) / size) * 100, 1)


def _network_addresses(data: dict[str, Any]) -> list[dict[str, Any]]:
    network = _system(data).get("network")
    return network if isinstance(network, list) else []


def _primary_network_address(data: dict[str, Any]) -> str | None:
    for item in _network_addresses(data):
        if isinstance(item, dict) and item.get("address"):
            return item["address"]
    return None


def _pc_status(data: dict[str, Any]) -> str:
    if _system(data):
        return "ok"
    if data.get("systemInfoError"):
        return "unavailable"
    return "unknown"


def _pc_status_attributes(data: dict[str, Any]) -> dict[str, Any]:
    system = _system(data)
    return {
        "error": data.get("systemInfoError") or "",
        "host": system.get("host"),
        "platform": system.get("platform"),
        "node_version": system.get("nodeVersion"),
        "port": system.get("port"),
        "updated_at": format_timestamp(system.get("at")),
        "updated_at_raw": system.get("at"),
    }


def _cpu_attributes(data: dict[str, Any]) -> dict[str, Any]:
    cpu = _cpu(data)
    return {
        "model": cpu.get("model"),
        "cores": cpu.get("cores"),
        "load_average": cpu.get("loadAverage"),
    }


def _memory_attributes(data: dict[str, Any]) -> dict[str, Any]:
    memory = _memory(data)
    return {
        "total": memory.get("total"),
        "used": memory.get("used"),
        "free": memory.get("free"),
    }


def _disk_attributes(data: dict[str, Any]) -> dict[str, Any]:
    drive = _first_drive(data)
    disk = _system(data).get("disk")
    error = disk.get("error") if isinstance(disk, dict) else ""
    return {
        "drive": drive.get("id"),
        "name": drive.get("name"),
        "size": drive.get("size"),
        "free": drive.get("free"),
        "used": (drive.get("size") - drive.get("free")) if drive.get("size") and drive.get("free") is not None else None,
        "error": error,
    }


def _network_attributes(data: dict[str, Any]) -> dict[str, Any]:
    return {"addresses": _network_addresses(data)}


def _last_error(data: dict[str, Any]) -> str:
    for value in (
        _display(data).get("lastControlError"),
        data.get("screen", {}).get("lastError"),
        data.get("browser", {}).get("lastError"),
        _browser(data).get("lastError"),
        _update(data).get("lastError"),
        _smart(data).get("lastProblem"),
        data.get("systemInfoError"),
    ):
        if value:
            return str(value)
    return ""


def _latest_photo(data: dict[str, Any]) -> dict[str, Any] | None:
    photos = data.get("photos", [])
    if not isinstance(photos, list) or not photos:
        return None
    return max((photo for photo in photos if isinstance(photo, dict)), key=lambda photo: photo.get("addedAt") or "", default=None)


def _latest_photo_attributes(data: dict[str, Any]) -> dict[str, Any]:
    photo = _latest_photo(data) or {}
    return {
        "id": photo.get("id"),
        "name": photo.get("name"),
        "uploaded_by": photo.get("uploadedBy"),
        "uploaded_at": format_timestamp(photo.get("addedAt")),
        "uploaded_at_raw": photo.get("addedAt"),
        "favorite": photo.get("favorite"),
        "visible": photo.get("visible"),
    }


SENSORS: tuple[dict[str, Any], ...] = (
    {"key": "app_version", "name": "Version", "value_fn": lambda data: data.get("server", {}).get("appVersion")},
    {"key": "mode", "name": "Mode", "value_fn": lambda data: _config(data).get("mode")},
    {"key": "screen", "name": "Screen", "value_fn": _screen},
    {"key": "photo_count", "name": "Photos", "value_fn": lambda data: len(data.get("photos", []))},
    {"key": "active_page", "name": "Active page", "value_fn": _active_page},
    {
        "key": "current_photo",
        "name": "Current photo",
        "value_fn": lambda data: _display(data).get("currentPhotoName") or _display(data).get("currentPhotoId") or "",
        "icon": "mdi:image",
        "attributes_fn": lambda data: {
            "id": _display(data).get("currentPhotoId"),
            "index": _display(data).get("currentPhotoIndex"),
            "photo_count": _display(data).get("photoCount"),
            "last_seen_at": format_timestamp(_display(data).get("lastSeenAt")),
            "last_seen_at_raw": _display(data).get("lastSeenAt"),
        },
    },
    {
        "key": "latest_upload",
        "name": "Latest upload",
        "value_fn": lambda data: format_timestamp((_latest_photo(data) or {}).get("addedAt")),
        "icon": "mdi:cloud-upload-outline",
        "attributes_fn": _latest_photo_attributes,
    },
    {
        "key": "current_url",
        "name": "Current URL",
        "value_fn": lambda data: _browser(data).get("activeUrl") or data.get("browser", {}).get("lastUrl") or _active_page(data),
        "icon": "mdi:web",
        "requires_system": True,
    },
    {
        "key": "browser_status",
        "name": "Kiosk browser",
        "value_fn": lambda data: "online" if _browser(data).get("devtoolsAvailable") else "unknown",
        "icon": "mdi:monitor-dashboard",
        "attributes_fn": lambda data: _browser(data),
        "requires_system": True,
    },
    {
        "key": "browser_window_state",
        "name": "Browser window state",
        "value_fn": lambda data: _browser(data).get("windowState") or "",
        "icon": "mdi:fullscreen",
        "requires_system": True,
    },
    {
        "key": "display_last_seen",
        "name": "Display last seen",
        "value_fn": lambda data: format_timestamp(_display(data).get("lastSeenAt")),
        "icon": "mdi:eye-check-outline",
        "attributes_fn": lambda data: {
            "last_seen_at_raw": _display(data).get("lastSeenAt"),
        },
    },
    {
        "key": "display_uptime",
        "name": "Display uptime",
        "value_fn": lambda data: format_duration(_display(data).get("displayUptimeSeconds")),
        "icon": "mdi:timer-sand",
        "attributes_fn": lambda data: {
            "seconds": _display(data).get("displayUptimeSeconds"),
        },
    },
    {
        "key": "display_slide_nodes",
        "name": "Display slide nodes",
        "value_fn": lambda data: _display(data).get("slideNodeCount"),
        "icon": "mdi:image-multiple-outline",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "key": "display_js_heap_used",
        "name": "Display JS heap used",
        "value_fn": lambda data: _display(data).get("jsHeapUsed"),
        "unit": UnitOfInformation.BYTES,
        "icon": "mdi:memory",
        "state_class": SensorStateClass.MEASUREMENT,
        "attributes_fn": lambda data: {
            "heap_limit": _display(data).get("jsHeapLimit"),
        },
    },
    {
        "key": "update_status",
        "name": "Update status",
        "value_fn": lambda data: _update(data).get("status"),
        "icon": "mdi:update",
        "attributes_fn": lambda data: _update(data),
    },
    {
        "key": "last_error",
        "name": "Last error",
        "value_fn": _last_error,
        "icon": "mdi:alert-circle-outline",
    },
    {
        "key": "smart_slot",
        "name": "Smart slot",
        "value_fn": lambda data: _smart(data).get("lastSlot"),
        "icon": "mdi:sun-clock-outline",
        "attributes_fn": lambda data: _smart(data),
    },
    {
        "key": "self_healing_last_action",
        "name": "Self-healing last action",
        "value_fn": lambda data: _smart(data).get("lastSelfHealAction"),
        "icon": "mdi:auto-fix",
        "attributes_fn": lambda data: _smart(data),
    },
    {
        "key": "pc_status",
        "name": "PC status",
        "value_fn": _pc_status,
        "icon": "mdi:desktop-tower-monitor",
        "attributes_fn": _pc_status_attributes,
    },
    {
        "key": "pc_uptime",
        "name": "PC uptime",
        "value_fn": lambda data: format_duration(_system(data).get("uptimeSeconds")),
        "icon": "mdi:clock-outline",
        "attributes_fn": lambda data: {
            "seconds": _system(data).get("uptimeSeconds"),
        },
        "requires_system": True,
    },
    {
        "key": "pc_cpu_usage",
        "name": "PC CPU usage",
        "value_fn": lambda data: _cpu(data).get("usagePercent"),
        "unit": PERCENTAGE,
        "icon": "mdi:cpu-64-bit",
        "state_class": SensorStateClass.MEASUREMENT,
        "attributes_fn": _cpu_attributes,
        "requires_system": True,
    },
    {
        "key": "pc_memory_usage",
        "name": "PC memory usage",
        "value_fn": lambda data: _memory(data).get("usedPercent"),
        "unit": PERCENTAGE,
        "icon": "mdi:memory",
        "state_class": SensorStateClass.MEASUREMENT,
        "attributes_fn": _memory_attributes,
        "requires_system": True,
    },
    {
        "key": "pc_disk_usage",
        "name": "PC disk usage",
        "value_fn": _disk_used_percent,
        "unit": PERCENTAGE,
        "icon": "mdi:harddisk",
        "state_class": SensorStateClass.MEASUREMENT,
        "attributes_fn": _disk_attributes,
        "requires_system": True,
    },
    {
        "key": "pc_process_memory",
        "name": "Frame process memory",
        "value_fn": lambda data: _process_memory(data).get("rss"),
        "unit": UnitOfInformation.BYTES,
        "icon": "mdi:application-cog",
        "state_class": SensorStateClass.MEASUREMENT,
        "requires_system": True,
    },
    {
        "key": "pc_process_uptime",
        "name": "Frame process uptime",
        "value_fn": lambda data: format_duration(_process(data).get("uptimeSeconds")),
        "icon": "mdi:timer-play-outline",
        "attributes_fn": lambda data: {
            "seconds": _process(data).get("uptimeSeconds"),
        },
        "requires_system": True,
    },
    {
        "key": "pc_network_address",
        "name": "PC network address",
        "value_fn": _primary_network_address,
        "icon": "mdi:lan",
        "attributes_fn": _network_attributes,
        "requires_system": True,
    },
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DigitalFrameSensor(coordinator, definition)
        for definition in SENSORS
    )


class DigitalFrameSensor(DigitalFrameEntity, SensorEntity):
    def __init__(
        self,
        coordinator: DigitalFrameCoordinator,
        definition: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, definition["key"], definition["name"])
        self._value_fn: Callable[[dict[str, Any]], Any] = definition["value_fn"]
        self._attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = definition.get("attributes_fn")
        self._requires_system = bool(definition.get("requires_system"))
        self._attr_icon = definition.get("icon")
        self._attr_native_unit_of_measurement = definition.get("unit")
        self._attr_state_class = definition.get("state_class")

    @property
    def available(self) -> bool:
        if self._requires_system and not _system(self.coordinator.data or {}):
            return False
        return super().available

    @property
    def native_value(self) -> Any:
        return self._value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self._attributes_fn is None:
            return None
        return self._attributes_fn(self.coordinator.data or {})
