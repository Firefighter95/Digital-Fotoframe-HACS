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


def _nested(data: dict[str, Any], *keys: str) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _has_problem(data: dict[str, Any]) -> bool:
    return any(
        bool(value)
        for value in (
            _nested(data, "display", "lastControlError"),
            _nested(data, "screen", "lastError"),
            _nested(data, "browser", "lastError"),
            _nested(data, "systemInfo", "browser", "lastError"),
            _nested(data, "update", "lastError"),
            data.get("systemInfoError"),
        )
    )


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
        self._async_fire_state_events(data)
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

    def _event_data(self, data: dict[str, Any], **extra: Any) -> dict[str, Any]:
        config = data.get("config") if isinstance(data.get("config"), dict) else {}
        return {
            "entry_id": self.config_entry.entry_id,
            "name": self.config_entry.title,
            "device_name": config.get("deviceName") or self.config_entry.title,
            **extra,
        }

    def _async_fire_state_events(self, data: dict[str, Any]) -> None:
        old = self.data or {}
        if not old:
            return

        old_mode = _nested(old, "config", "mode")
        new_mode = _nested(data, "config", "mode")
        if old_mode != new_mode:
            self.hass.bus.async_fire(
                "digital_frame_mode_changed",
                self._event_data(data, old_mode=old_mode, new_mode=new_mode),
            )

        old_photo_id = _nested(old, "display", "currentPhotoId")
        new_photo_id = _nested(data, "display", "currentPhotoId")
        if old_photo_id != new_photo_id and new_photo_id:
            self.hass.bus.async_fire(
                "digital_frame_photo_changed",
                self._event_data(
                    data,
                    photo_id=new_photo_id,
                    photo_name=_nested(data, "display", "currentPhotoName"),
                    photo_index=_nested(data, "display", "currentPhotoIndex"),
                    photo_count=_nested(data, "display", "photoCount"),
                ),
            )

        old_update_status = _nested(old, "update", "status")
        new_update_status = _nested(data, "update", "status")
        if old_update_status != new_update_status:
            self.hass.bus.async_fire(
                "digital_frame_update_status_changed",
                self._event_data(data, old_status=old_update_status, new_status=new_update_status),
            )

        old_problem = _has_problem(old)
        new_problem = _has_problem(data)
        if old_problem != new_problem:
            self.hass.bus.async_fire(
                "digital_frame_problem_changed",
                self._event_data(data, active=new_problem),
            )
