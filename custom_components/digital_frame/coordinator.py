from __future__ import annotations

from datetime import timedelta
import json
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import DigitalFrameApi, DigitalFrameError
from .const import CONF_WEATHER_ENTITY, DOMAIN

_LOGGER = logging.getLogger(__name__)
SYSTEM_INFO_INTERVAL_SECONDS = 15
WEATHER_RESEND_INTERVAL_SECONDS = 300


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
            _nested(data, "smart", "lastProblem"),
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
        self._weather_last_payload = ""
        self._weather_last_push = 0.0

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_get_state()
        except DigitalFrameError as err:
            raise UpdateFailed(str(err)) from err
        await self._async_update_system_info(data)
        await self._async_update_weather(data)
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

    def _weather_entity_id(self) -> str:
        return str(self.config_entry.options.get(CONF_WEATHER_ENTITY) or "").strip()

    def _weather_payload(self, entity_id: str) -> dict[str, Any]:
        now = dt_util.utcnow().isoformat()
        if not entity_id:
            return {
                "available": False,
                "entityId": "",
                "name": "",
                "condition": "",
                "temperature": None,
                "temperatureUnit": "",
                "humidity": None,
                "windSpeed": None,
                "windSpeedUnit": "",
                "updatedAt": now,
            }

        state = self.hass.states.get(entity_id)
        if state is None:
            return {
                "available": False,
                "entityId": entity_id,
                "name": entity_id,
                "condition": "",
                "temperature": None,
                "temperatureUnit": "",
                "humidity": None,
                "windSpeed": None,
                "windSpeedUnit": "",
                "updatedAt": now,
            }

        attributes = state.attributes
        available = state.state not in ("unknown", "unavailable")
        units = getattr(self.hass.config, "units", None)
        temperature_unit = attributes.get("temperature_unit") or getattr(units, "temperature_unit", "")
        return {
            "available": available,
            "entityId": entity_id,
            "name": attributes.get("friendly_name") or entity_id,
            "condition": state.state if available else "",
            "temperature": attributes.get("temperature"),
            "temperatureUnit": str(temperature_unit or ""),
            "humidity": attributes.get("humidity"),
            "windSpeed": attributes.get("wind_speed"),
            "windSpeedUnit": str(attributes.get("wind_speed_unit") or ""),
            "updatedAt": now,
        }

    async def _async_update_weather(self, data: dict[str, Any]) -> None:
        payload = self._weather_payload(self._weather_entity_id())
        fingerprint = json.dumps(payload, sort_keys=True, default=str)
        now = time.monotonic()
        data["weather"] = payload
        if fingerprint == self._weather_last_payload and now - self._weather_last_push < WEATHER_RESEND_INTERVAL_SECONDS:
            return

        try:
            await self.api.async_update_weather(payload)
        except DigitalFrameError as err:
            data["weatherSyncError"] = str(err)
            return

        self._weather_last_payload = fingerprint
        self._weather_last_push = now

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
