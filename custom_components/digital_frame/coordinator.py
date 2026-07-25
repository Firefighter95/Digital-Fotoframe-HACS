from __future__ import annotations

from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DigitalFrameApi, DigitalFrameError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SYSTEM_INFO_INTERVAL_SECONDS = 15


class DigitalFrameCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, api: DigitalFrameApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=5),
        )
        self.config_entry = config_entry
        self.api = api
        self._system_info: dict[str, Any] | None = None
        self._system_info_error: str | None = None
        self._system_info_last_fetch = 0.0

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_get_state()
        except DigitalFrameError as err:
            raise UpdateFailed(str(err)) from err
        await self._async_update_system_info(data)
        return data

    async def _async_update_system_info(self, data: dict[str, Any]) -> None:
        now = time.monotonic()
        if now - self._system_info_last_fetch < SYSTEM_INFO_INTERVAL_SECONDS:
            data["systemInfo"] = self._system_info
            if self._system_info_error:
                data["systemInfoError"] = self._system_info_error
            return

        self._system_info_last_fetch = now
        try:
            response = await self.api.async_get_system_info()
        except DigitalFrameError as err:
            self._system_info_error = str(err)
        else:
            self._system_info = response.get("system") or {}
            self._system_info_error = None

        if self._system_info is not None:
            data["systemInfo"] = self._system_info
        if self._system_info_error:
            data["systemInfoError"] = self._system_info_error

    async def async_call_and_refresh(self, call) -> None:
        await call
        await self.async_request_refresh()
