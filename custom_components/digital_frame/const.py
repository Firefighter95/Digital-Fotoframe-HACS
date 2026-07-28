from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "digital_frame"
DEFAULT_NAME = "Digital Frame"
DEFAULT_HOST = "digital-frame.local"
DEFAULT_PORT = 8787
DEFAULT_ACTOR = "Home Assistant"

CONF_ACTOR = "actor"
CONF_PIN = "pin"

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.SELECT, Platform.TEXT]

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
