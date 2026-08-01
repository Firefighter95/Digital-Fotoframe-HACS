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
from .const import (
    CONF_F1_CURRENT_SESSION_ENTITY,
    CONF_F1_DRIVER_LIST_ENTITY,
    CONF_F1_DRIVER_POSITIONS_ENTITY,
    CONF_F1_RACE_LAP_ENTITY,
    CONF_F1_TRACK_STATUS_ENTITY,
    CONF_F1_TYRES_ENTITY,
    CONF_WEATHER_ENTITY,
    DEFAULT_F1_SENSOR_ENTITIES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
SYSTEM_INFO_INTERVAL_SECONDS = 15
WEATHER_RESEND_INTERVAL_SECONDS = 300
F1_RESEND_INTERVAL_SECONDS = 30


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


def _state_available(state: Any) -> bool:
    return state is not None and state.state not in ("unknown", "unavailable", "")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_int(value: Any, fallback: int | None = None) -> int | None:
    try:
        if value in (None, "", "unknown", "unavailable"):
            return fallback
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def _driver_number(driver: Any) -> str:
    if not isinstance(driver, dict):
        return ""
    return str(driver.get("racing_number") or driver.get("number") or driver.get("driver_number") or "").strip()


def _drivers_by_number(drivers: list[Any]) -> dict[str, dict[str, Any]]:
    by_number: dict[str, dict[str, Any]] = {}
    for driver in drivers:
        if not isinstance(driver, dict):
            continue
        number = _driver_number(driver)
        if number:
            by_number[number] = driver
    return by_number


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
        self._f1_last_payload = ""
        self._f1_last_push = 0.0

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_get_state()
        except DigitalFrameError as err:
            raise UpdateFailed(str(err)) from err
        await self._async_update_system_info(data)
        await self._async_update_weather(data)
        await self._async_update_f1(data)
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

    def _option_entity_id(self, key: str) -> str:
        return str(self.config_entry.options.get(key, DEFAULT_F1_SENSOR_ENTITIES.get(key, "")) or "").strip()

    def _state_payload(self, key: str) -> tuple[Any, dict[str, Any]]:
        entity_id = self._option_entity_id(key)
        state = self.hass.states.get(entity_id) if entity_id else None
        return state, dict(getattr(state, "attributes", {}) or {})

    def _f1_payload(self) -> dict[str, Any]:
        now = dt_util.utcnow().isoformat()
        positions_state, positions_attr = self._state_payload(CONF_F1_DRIVER_POSITIONS_ENTITY)
        driver_list_state, driver_list_attr = self._state_payload(CONF_F1_DRIVER_LIST_ENTITY)
        tyres_state, tyres_attr = self._state_payload(CONF_F1_TYRES_ENTITY)
        track_status_state, _ = self._state_payload(CONF_F1_TRACK_STATUS_ENTITY)
        session_state, session_attr = self._state_payload(CONF_F1_CURRENT_SESSION_ENTITY)
        lap_state, lap_attr = self._state_payload(CONF_F1_RACE_LAP_ENTITY)

        position_drivers = _as_list(positions_attr.get("drivers"))
        listed_drivers = _as_list(driver_list_attr.get("drivers"))
        tyre_drivers = _as_list(tyres_attr.get("drivers"))
        if not position_drivers and tyre_drivers:
            position_drivers = tyre_drivers
        if not position_drivers and listed_drivers:
            position_drivers = listed_drivers

        listed_by_number = _drivers_by_number(listed_drivers)
        tyres_by_number = _drivers_by_number(tyre_drivers)
        drivers: list[dict[str, Any]] = []
        for index, driver in enumerate(position_drivers[:30]):
            if not isinstance(driver, dict):
                continue
            number = _driver_number(driver)
            listed = listed_by_number.get(number, {})
            tyre = tyres_by_number.get(number, {})
            position = _safe_int(driver.get("current_position") or driver.get("position") or tyre.get("position"), index + 1) or index + 1
            compound = str(tyre.get("compound_short") or tyre.get("compound") or "").strip()
            stint_laps = _safe_int(tyre.get("stint_laps"))
            status = str(driver.get("status") or "").replace("_", " ").strip()
            gap = str(driver.get("gap_to_leader") or driver.get("interval_to_position_ahead") or "").strip()
            detail_parts = []
            if compound:
                tyre_label = compound
                if stint_laps is not None:
                    tyre_label = f"{tyre_label} {stint_laps}L"
                detail_parts.append(tyre_label)
            if status and status != "on track":
                detail_parts.append(status.title())
            if gap:
                detail_parts.append(gap)
            if not detail_parts and driver.get("team"):
                detail_parts.append(str(driver.get("team")))
            drivers.append(
                {
                    "number": number or str(index + 1),
                    "name": driver.get("name") or listed.get("name") or driver.get("full_name") or driver.get("tla") or f"Driver {index + 1}",
                    "abbr": driver.get("tla") or listed.get("tla") or driver.get("abbr") or "",
                    "position": position,
                    "gap": " - ".join(detail_parts),
                    "color": driver.get("team_color") or listed.get("team_color") or tyre.get("team_color") or "#e43d4f",
                }
            )

        drivers.sort(key=lambda item: _safe_int(item.get("position"), 99) or 99)
        session_label = str(session_state.state if _state_available(session_state) else session_attr.get("last_label") or "F1").strip()
        meeting = str(session_attr.get("meeting_name") or session_attr.get("circuit_short_name") or "").strip()
        track_status = str(track_status_state.state if _state_available(track_status_state) else "").strip()
        current_lap = _safe_int(getattr(lap_state, "state", None), _safe_int(getattr(positions_state, "state", None)))
        total_laps = _safe_int(lap_attr.get("total_laps"), _safe_int(positions_attr.get("total_laps")))
        subtitle_parts = [part for part in (meeting, track_status) if part]
        if current_lap is not None:
            lap_text = f"Lap {current_lap}"
            if total_laps is not None:
                lap_text = f"{lap_text}/{total_laps}"
            subtitle_parts.append(lap_text)
        available = bool(drivers) and (_state_available(positions_state) or _state_available(driver_list_state) or _state_available(tyres_state))
        return {
            "title": f"{session_label} - F1 Sensor" if session_label else "F1 Sensor",
            "subtitle": " - ".join(subtitle_parts) or "Home Assistant f1_sensor",
            "source": "home-assistant-f1-sensor",
            "drivers": drivers,
            "track": [],
            "note": "" if available else "Geen live F1 Sensor data beschikbaar.",
            "available": available,
            "updatedAt": now,
        }

    async def _async_update_f1(self, data: dict[str, Any]) -> None:
        payload = self._f1_payload()
        data["f1Sync"] = {
            "available": payload.get("available"),
            "drivers": len(payload.get("drivers", [])),
            "updatedAt": payload.get("updatedAt"),
            "source": payload.get("source"),
        }
        if not payload.get("drivers"):
            return

        fingerprint = json.dumps(payload, sort_keys=True, default=str)
        now = time.monotonic()
        if fingerprint == self._f1_last_payload and now - self._f1_last_push < F1_RESEND_INTERVAL_SECONDS:
            return

        try:
            await self.api.async_update_f1(payload)
        except DigitalFrameError as err:
            data["f1SyncError"] = str(err)
            return

        self._f1_last_payload = fingerprint
        self._f1_last_push = now

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
