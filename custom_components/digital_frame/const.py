from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "digital_frame"
DEFAULT_NAME = "Digital Frame"
DEFAULT_HOST = "digital-frame.local"
DEFAULT_PORT = 8787
DEFAULT_ACTOR = "Home Assistant"

CONF_ACTOR = "actor"
CONF_PIN = "pin"

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
    "off": "Off",
}
