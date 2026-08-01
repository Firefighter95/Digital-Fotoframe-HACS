from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "digital_frame"
DEFAULT_NAME = "Digital Frame"
DEFAULT_HOST = "digital-frame.local"
DEFAULT_PORT = 8787
DEFAULT_ACTOR = "Home Assistant"

CONF_ACTOR = "actor"
CONF_PIN = "pin"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_F1_DRIVER_POSITIONS_ENTITY = "f1_driver_positions_entity"
CONF_F1_DRIVER_LIST_ENTITY = "f1_driver_list_entity"
CONF_F1_TYRES_ENTITY = "f1_tyres_entity"
CONF_F1_TRACK_STATUS_ENTITY = "f1_track_status_entity"
CONF_F1_CURRENT_SESSION_ENTITY = "f1_current_session_entity"
CONF_F1_RACE_LAP_ENTITY = "f1_race_lap_entity"
CONF_F1_DASHBOARD_URL = "f1_dashboard_url"

DEFAULT_F1_SENSOR_ENTITIES = {
    CONF_F1_DRIVER_POSITIONS_ENTITY: "sensor.f1_driver_positions",
    CONF_F1_DRIVER_LIST_ENTITY: "sensor.f1_driver_list",
    CONF_F1_TYRES_ENTITY: "sensor.f1_current_tyres",
    CONF_F1_TRACK_STATUS_ENTITY: "sensor.f1_track_status",
    CONF_F1_CURRENT_SESSION_ENTITY: "sensor.f1_current_session",
    CONF_F1_RACE_LAP_ENTITY: "sensor.f1_race_lap_count",
}

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.IMAGE,
    Platform.NOTIFY,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
    Platform.UPDATE,
]

MODE_OPTIONS = {
    "slideshow": "Photos",
    "dashboard": "Meters",
    "f1": "F1 map",
    "message": "Message",
    "iframe": "Web page",
    "blank": "Blank screen",
    "qr": "Admin QR",
}

SMART_MODE_OPTIONS = {
    "slideshow": "Photos",
    "dashboard": "Meters",
    "iframe": "Web page",
    "f1": "F1 map",
    "message": "Message",
    "qr": "Admin QR",
    "blank": "Blank screen",
}

PHOTO_SOURCE_OPTIONS = {
    "all": "All visible photos",
    "favorites": "Favorites only",
}

CLOCK_POSITION_OPTIONS = {
    "top-right": "Top right",
    "top-left": "Top left",
    "bottom-right": "Bottom right",
    "bottom-left": "Bottom left",
}

PHOTO_FIT_OPTIONS = {
    "cover": "Fill screen",
    "contain": "Fit entire photo",
}

F1_PROVIDER_OPTIONS = {
    "openf1": "OpenF1 live",
    "homeassistant": "Home Assistant f1_sensor",
    "off": "Manual/Home Assistant only",
}
