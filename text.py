{
  "config": {
    "step": {
      "user": {
        "title": "Digital Frame",
        "description": "Connect Home Assistant to the photo frame server.",
        "data": {
          "name": "Name",
          "host": "Host",
          "port": "Port",
          "pin": "Admin PIN",
          "actor": "Logbook name"
        }
      }
    },
    "error": {
      "cannot_connect": "Cannot connect to the photo frame.",
      "invalid_auth": "The PIN is not correct.",
      "unknown": "Unknown error."
    },
    "abort": {
      "already_configured": "This photo frame is already configured."
    }
  }
}
