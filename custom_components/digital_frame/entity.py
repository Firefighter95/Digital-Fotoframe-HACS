from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DigitalFrameCoordinator


class DigitalFrameEntity(CoordinatorEntity[DigitalFrameCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DigitalFrameCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_name = name

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        server = data.get("server", {})
        admin_urls = server.get("adminUrls") or []
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name=self.coordinator.config_entry.title,
            manufacturer="LAN Digital Frame",
            model="Windows fotolijst",
            sw_version=server.get("appVersion"),
            configuration_url=admin_urls[0] if admin_urls else None,
        )
