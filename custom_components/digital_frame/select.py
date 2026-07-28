from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CLOCK_POSITION_OPTIONS, DOMAIN, F1_PROVIDER_OPTIONS, MODE_OPTIONS, PHOTO_FIT_OPTIONS, PHOTO_SOURCE_OPTIONS
from .coordinator import DigitalFrameCoordinator
from .entity import DigitalFrameEntity


@dataclass(frozen=True)
class DigitalFrameConfigSelectDescription:
    key: str
    name: str
    config_key: str
    options: dict[str, str]
    icon: str


CONFIG_SELECTS: tuple[DigitalFrameConfigSelectDescription, ...] = (
    DigitalFrameConfigSelectDescription("clock_position_select", "Clock position", "clockPosition", CLOCK_POSITION_OPTIONS, "mdi:clock-edit-outline"),
    DigitalFrameConfigSelectDescription("photo_fit_select", "Photo fit", "photoFit", PHOTO_FIT_OPTIONS, "mdi:fit-to-screen-outline"),
    DigitalFrameConfigSelectDescription("f1_provider_select", "F1 provider", "f1Provider", F1_PROVIDER_OPTIONS, "mdi:flag-checkered"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DigitalFrameCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            DigitalFrameModeSelect(coordinator),
            DigitalFrameModeItemSelect(coordinator),
            DigitalFramePhotoSourceSelect(coordinator),
            DigitalFramePageSelect(coordinator),
            *[DigitalFrameConfigSelect(coordinator, description) for description in CONFIG_SELECTS],
        ]
    )


class DigitalFrameModeSelect(DigitalFrameEntity, SelectEntity):
    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "mode_select", "Mode")

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "display" in permissions and super().available

    @property
    def options(self) -> list[str]:
        return list(MODE_OPTIONS.values())

    @property
    def current_option(self) -> str | None:
        mode = (self.coordinator.data or {}).get("config", {}).get("mode")
        return MODE_OPTIONS.get(mode)

    async def async_select_option(self, option: str) -> None:
        mode = _key_for_label(MODE_OPTIONS, option)
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_set_mode(mode))


class DigitalFramePhotoSourceSelect(DigitalFrameEntity, SelectEntity):
    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "photo_source_select", "Photo selection")

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "settings" in permissions and super().available

    @property
    def options(self) -> list[str]:
        return list(PHOTO_SOURCE_OPTIONS.values())

    @property
    def current_option(self) -> str | None:
        source = (self.coordinator.data or {}).get("config", {}).get("photoSource")
        return PHOTO_SOURCE_OPTIONS.get(source)

    async def async_select_option(self, option: str) -> None:
        source = _key_for_label(PHOTO_SOURCE_OPTIONS, option)
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_set_photo_source(source))


class DigitalFrameModeItemSelect(DigitalFrameEntity, SelectEntity):
    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "mode_item_select", "Mode list")

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "display" in permissions and super().available

    @property
    def options(self) -> list[str]:
        options, _ = self._mode_item_options()
        return options

    @property
    def current_option(self) -> str | None:
        _, by_id = self._mode_item_options()
        for item in (self.coordinator.data or {}).get("modeItems", []):
            if item.get("active") is True:
                return by_id.get(item.get("id"))
        return None

    async def async_select_option(self, option: str) -> None:
        label_to_id = {label: item_id for item_id, label in self._mode_item_options()[1].items()}
        item_id = label_to_id.get(option)
        if not item_id:
            raise HomeAssistantError(f"Onbekende fotolijstmodus: {option}")
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_show_mode_item(item_id))

    def _mode_item_options(self) -> tuple[list[str], dict[str, str]]:
        items = (self.coordinator.data or {}).get("modeItems", [])
        used: set[str] = set()
        options: list[str] = []
        by_id: dict[str, str] = {}
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue
            label = item.get("name") or item_id
            if label in used:
                label = f"{label} ({item_id})"
            used.add(label)
            options.append(label)
            by_id[item_id] = label
        return options, by_id


class DigitalFramePageSelect(DigitalFrameEntity, SelectEntity):
    def __init__(self, coordinator: DigitalFrameCoordinator) -> None:
        super().__init__(coordinator, "page_select", "Page")

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "display" in permissions and super().available

    @property
    def options(self) -> list[str]:
        options, _ = self._page_options()
        return options

    @property
    def current_option(self) -> str | None:
        _, by_id = self._page_options()
        page_id = (self.coordinator.data or {}).get("iframe", {}).get("pageId")
        return by_id.get(page_id)

    async def async_select_option(self, option: str) -> None:
        label_to_id = {label: page_id for page_id, label in self._page_options()[1].items()}
        page_id = label_to_id.get(option)
        if not page_id:
            raise HomeAssistantError(f"Onbekende fotolijstpagina: {option}")
        await self.coordinator.async_call_and_refresh(self.coordinator.api.async_show_page(page_id))

    def _page_options(self) -> tuple[list[str], dict[str, str]]:
        pages = (self.coordinator.data or {}).get("pages", [])
        used: set[str] = set()
        options: list[str] = []
        by_id: dict[str, str] = {}
        for page in pages:
            page_id = page.get("id")
            if not page_id:
                continue
            label = page.get("name") or page_id
            if label in used:
                label = f"{label} ({page_id})"
            used.add(label)
            options.append(label)
            by_id[page_id] = label
        return options, by_id


class DigitalFrameConfigSelect(DigitalFrameEntity, SelectEntity):
    def __init__(self, coordinator: DigitalFrameCoordinator, description: DigitalFrameConfigSelectDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description
        self._attr_icon = description.icon

    @property
    def available(self) -> bool:
        permissions = (self.coordinator.data or {}).get("currentUser", {}).get("permissions", [])
        return "settings" in permissions and super().available

    @property
    def options(self) -> list[str]:
        return list(self.entity_description.options.values())

    @property
    def current_option(self) -> str | None:
        value = (self.coordinator.data or {}).get("config", {}).get(self.entity_description.config_key)
        return self.entity_description.options.get(value)

    async def async_select_option(self, option: str) -> None:
        value = _key_for_label(self.entity_description.options, option)
        await self.coordinator.async_call_and_refresh(
            self.coordinator.api.async_update_config(**{self.entity_description.config_key: value})
        )


def _key_for_label(options: dict[str, str], label: str) -> str:
    for key, value in options.items():
        if label == value or label == key:
            return key
    raise HomeAssistantError(f"Onbekende optie: {label}")
