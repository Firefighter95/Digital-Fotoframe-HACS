from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import CONF_ACTOR, CONF_PIN, DOMAIN

TO_REDACT = {
    CONF_ACTOR,
    CONF_HOST,
    CONF_PIN,
    CONF_PORT,
    "activeUrl",
    "adminPin",
    "configuration_url",
    "lastUrl",
    "url",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "state": async_redact_data(coordinator.data or {}, TO_REDACT),
    }
