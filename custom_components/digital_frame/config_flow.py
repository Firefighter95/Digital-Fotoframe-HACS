from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DigitalFrameApi, DigitalFrameAuthError, DigitalFrameCannotConnect, DigitalFrameError
from .const import CONF_ACTOR, CONF_PIN, CONF_WEATHER_ENTITY, DEFAULT_ACTOR, DEFAULT_HOST, DEFAULT_NAME, DEFAULT_PORT, DOMAIN


class DigitalFrameConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return DigitalFrameOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = DigitalFrameApi(
                session,
                user_input[CONF_HOST],
                user_input.get(CONF_PORT, DEFAULT_PORT),
                user_input[CONF_PIN],
                user_input.get(CONF_ACTOR, DEFAULT_ACTOR),
            )

            try:
                state = await api.async_get_state()
            except DigitalFrameCannotConnect:
                errors["base"] = "cannot_connect"
            except DigitalFrameAuthError:
                errors["base"] = "invalid_auth"
            except DigitalFrameError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"{api.host}:{api.port}")
                self._abort_if_unique_id_configured()
                title = (
                    user_input.get(CONF_NAME)
                    or state.get("config", {}).get("deviceName")
                    or DEFAULT_NAME
                )
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_NAME: title,
                        CONF_HOST: api.host,
                        CONF_PORT: api.port,
                        CONF_PIN: user_input[CONF_PIN],
                        CONF_ACTOR: user_input.get(CONF_ACTOR, DEFAULT_ACTOR),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                    vol.Required(CONF_HOST, default=DEFAULT_HOST): cv.string,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                    vol.Required(CONF_PIN): cv.string,
                    vol.Optional(CONF_ACTOR, default=DEFAULT_ACTOR): cv.string,
                }
            ),
            errors=errors,
        )


class DigitalFrameOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            weather_entity = str(user_input.get(CONF_WEATHER_ENTITY) or "").strip()
            return self.async_create_entry(title="", data={CONF_WEATHER_ENTITY: weather_entity})

        options = self.config_entry.options
        weather_entity = options.get(CONF_WEATHER_ENTITY, "")
        field = (
            vol.Optional(CONF_WEATHER_ENTITY, default=weather_entity)
            if weather_entity
            else vol.Optional(CONF_WEATHER_ENTITY)
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    field: selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="weather")
                    ),
                }
            ),
        )
