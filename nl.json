from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DigitalFrameApi, DigitalFrameError
from .const import (
    CONF_ACTOR,
    CONF_PIN,
    DEFAULT_ACTOR,
    DEFAULT_PORT,
    DOMAIN,
    MODE_OPTIONS,
    PLATFORMS,
)
from .coordinator import DigitalFrameCoordinator

SERVICE_SHOW_MESSAGE = "show_message"
SERVICE_SEND_MESSAGE = "send_message"
SERVICE_SHOW_URL = "show_url"
SERVICE_SHOW_PAGE = "show_page"
SERVICE_SAVE_PAGE = "save_page"
SERVICE_DELETE_PAGE = "delete_page"
SERVICE_SCREEN_ON = "screen_on"
SERVICE_SCREEN_OFF = "screen_off"
SERVICE_SHOW_MODE = "show_mode"
SERVICE_SHOW_MODE_ITEM = "show_mode_item"
SERVICE_RESTART_PC = "restart_pc"
SERVICE_SHUTDOWN_PC = "shutdown_pc"
SERVICE_CANCEL_SHUTDOWN = "cancel_shutdown"
SERVICE_RELOAD_DISPLAY = "reload_display"
SERVICE_FORCE_FULLSCREEN = "force_fullscreen"
SERVICE_NEXT_PHOTO = "next_photo"
SERVICE_PREVIOUS_PHOTO = "previous_photo"
SERVICE_IDENTIFY = "identify"
SERVICE_RESTART_KIOSK = "restart_kiosk"
SERVICE_APPLY_UPDATE = "apply_update"
SERVICE_SHOW_ADMIN_QR = "show_admin_qr"
SERVICE_APPLY_SMART_MODE = "apply_smart_mode"

ENTRY_FIELD = {vol.Optional("entry_id"): cv.string}

SHOW_MESSAGE_SCHEMA = vol.Schema(
    {
        **ENTRY_FIELD,
        vol.Optional("title", default="Message"): cv.string,
        vol.Required("message"): cv.string,
        vol.Optional("duration", default=60): vol.All(vol.Coerce(int), vol.Range(min=0, max=86400)),
        vol.Optional("accent", default="#d5a849"): cv.string,
        vol.Optional("priority", default="normal"): vol.In(["low", "normal", "high", "critical"]),
    }
)
SHOW_URL_SCHEMA = vol.Schema({**ENTRY_FIELD, vol.Required("url"): cv.url})
SHOW_PAGE_SCHEMA = vol.Schema({**ENTRY_FIELD, vol.Required("page_id"): cv.string})
SHOW_MODE_ITEM_SCHEMA = vol.Schema({**ENTRY_FIELD, vol.Required("mode_item_id"): cv.string})
SAVE_PAGE_SCHEMA = vol.Schema(
    {
        **ENTRY_FIELD,
        vol.Required("name"): cv.string,
        vol.Required("url"): cv.url,
        vol.Optional("page_id"): cv.string,
    }
)
DELETE_PAGE_SCHEMA = SHOW_PAGE_SCHEMA
SHOW_MODE_SCHEMA = vol.Schema({**ENTRY_FIELD, vol.Required("mode"): vol.In(list(MODE_OPTIONS))})
ENTRY_ONLY_SCHEMA = vol.Schema(ENTRY_FIELD)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    _async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = {**entry.data, **entry.options}
    session = async_get_clientsession(hass)
    api = DigitalFrameApi(
        session,
        data[CONF_HOST],
        data.get(CONF_PORT, DEFAULT_PORT),
        data[CONF_PIN],
        data.get(CONF_ACTOR, DEFAULT_ACTOR),
    )
    coordinator = DigitalFrameCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _coordinator_from_call(hass: HomeAssistant, call: ServiceCall) -> DigitalFrameCoordinator:
    coordinators: dict[str, DigitalFrameCoordinator] = hass.data.get(DOMAIN, {})
    entry_id = call.data.get("entry_id")
    if entry_id:
        coordinator = coordinators.get(entry_id)
        if coordinator:
            return coordinator
        raise HomeAssistantError(f"No Digital Frame found for entry_id {entry_id}.")

    if coordinators:
        return next(iter(coordinators.values()))
    raise HomeAssistantError("No Digital Frame configured.")


async def _run_frame_call(
    hass: HomeAssistant,
    call: ServiceCall,
    api_call: Callable[[DigitalFrameApi], Awaitable[dict[str, Any]]],
) -> None:
    coordinator = _coordinator_from_call(hass, call)
    try:
        await coordinator.async_call_and_refresh(api_call(coordinator.api))
    except DigitalFrameError as err:
        raise HomeAssistantError(str(err)) from err


def _async_register_services(hass: HomeAssistant) -> None:
    async def send_message(call: ServiceCall) -> None:
        await _run_frame_call(
            hass,
            call,
            lambda api: api.async_show_message(
                call.data["title"],
                call.data["message"],
                call.data["duration"],
                call.data["accent"],
                call.data["priority"],
            ),
        )

    async def show_message(call: ServiceCall) -> None:
        await send_message(call)

    async def show_url(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_show_url(call.data["url"]))

    async def show_page(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_show_page(call.data["page_id"]))

    async def show_mode_item(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_show_mode_item(call.data["mode_item_id"]))

    async def save_page(call: ServiceCall) -> None:
        await _run_frame_call(
            hass,
            call,
            lambda api: api.async_save_page(
                call.data["name"],
                call.data["url"],
                call.data.get("page_id"),
            ),
        )

    async def delete_page(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_delete_page(call.data["page_id"]))

    async def screen_on(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_set_screen("on"))

    async def screen_off(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_set_screen("off"))

    async def show_mode(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_set_mode(call.data["mode"]))

    async def restart_pc(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_system_power("restart"))

    async def shutdown_pc(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_system_power("shutdown"))

    async def cancel_shutdown(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_system_power("cancel"))

    async def reload_display(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_display_control("reload"))

    async def force_fullscreen(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_display_control("force_fullscreen"))

    async def next_photo(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_display_control("next_photo"))

    async def previous_photo(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_display_control("previous_photo"))

    async def identify(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_display_control("identify"))

    async def restart_kiosk(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_display_control("restart_kiosk"))

    async def apply_update(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_apply_update())

    async def show_admin_qr(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_display_control("show_admin_qr"))

    async def apply_smart_mode(call: ServiceCall) -> None:
        await _run_frame_call(hass, call, lambda api: api.async_display_control("apply_smart_mode"))

    def register_once(service: str, handler: Callable[[ServiceCall], Awaitable[None]], schema: vol.Schema) -> None:
        if not hass.services.has_service(DOMAIN, service):
            hass.services.async_register(DOMAIN, service, handler, schema=schema)

    register_once(SERVICE_SHOW_MESSAGE, show_message, SHOW_MESSAGE_SCHEMA)
    register_once(SERVICE_SEND_MESSAGE, send_message, SHOW_MESSAGE_SCHEMA)
    register_once(SERVICE_SHOW_URL, show_url, SHOW_URL_SCHEMA)
    register_once(SERVICE_SHOW_PAGE, show_page, SHOW_PAGE_SCHEMA)
    register_once(SERVICE_SHOW_MODE_ITEM, show_mode_item, SHOW_MODE_ITEM_SCHEMA)
    register_once(SERVICE_SAVE_PAGE, save_page, SAVE_PAGE_SCHEMA)
    register_once(SERVICE_DELETE_PAGE, delete_page, DELETE_PAGE_SCHEMA)
    register_once(SERVICE_SCREEN_ON, screen_on, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_SCREEN_OFF, screen_off, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_SHOW_MODE, show_mode, SHOW_MODE_SCHEMA)
    register_once(SERVICE_RESTART_PC, restart_pc, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_SHUTDOWN_PC, shutdown_pc, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_CANCEL_SHUTDOWN, cancel_shutdown, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_RELOAD_DISPLAY, reload_display, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_FORCE_FULLSCREEN, force_fullscreen, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_NEXT_PHOTO, next_photo, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_PREVIOUS_PHOTO, previous_photo, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_IDENTIFY, identify, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_RESTART_KIOSK, restart_kiosk, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_APPLY_UPDATE, apply_update, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_SHOW_ADMIN_QR, show_admin_qr, ENTRY_ONLY_SCHEMA)
    register_once(SERVICE_APPLY_SMART_MODE, apply_smart_mode, ENTRY_ONLY_SCHEMA)
