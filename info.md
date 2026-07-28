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
  },
  "entity": {
    "binary_sensor": {
      "display_connected": {
        "name": "Display connected"
      },
      "kiosk_browser_connected": {
        "name": "Kiosk browser connected"
      },
      "browser_fullscreen": {
        "name": "Browser fullscreen"
      },
      "problem": {
        "name": "Problem"
      }
    },
    "button": {
      "reload_display": {
        "name": "Reload display"
      },
      "force_fullscreen": {
        "name": "Force fullscreen"
      },
      "next_photo": {
        "name": "Next photo"
      },
      "previous_photo": {
        "name": "Previous photo"
      },
      "identify": {
        "name": "Identify"
      },
      "show_admin_qr": {
        "name": "Show admin QR"
      },
      "apply_smart_mode": {
        "name": "Apply smart mode"
      },
      "restart_kiosk": {
        "name": "Restart kiosk browser"
      },
      "restart_pc": {
        "name": "Restart PC"
      },
      "shutdown_pc": {
        "name": "Shut down PC"
      },
      "cancel_shutdown": {
        "name": "Cancel shutdown"
      },
      "apply_update": {
        "name": "Apply update"
      }
    },
    "image": {
      "status_image": {
        "name": "Status image"
      }
    },
    "notify": {
      "notify": {
        "name": "Notify"
      }
    },
    "number": {
      "slide_seconds": {
        "name": "Slideshow interval"
      },
      "photo_overlay": {
        "name": "Photo dark overlay"
      },
      "clock_size": {
        "name": "Clock size"
      },
      "clock_backdrop_opacity": {
        "name": "Clock backdrop opacity"
      },
      "page_fallback_seconds": {
        "name": "Page fallback seconds"
      }
    },
    "select": {
      "clock_position_select": {
        "name": "Clock position"
      },
      "photo_fit_select": {
        "name": "Photo fit"
      },
      "f1_provider_select": {
        "name": "F1 provider"
      },
      "smart_morning_mode_select": {
        "name": "Smart morning mode"
      },
      "smart_day_mode_select": {
        "name": "Smart day mode target"
      },
      "smart_evening_mode_select": {
        "name": "Smart evening mode"
      },
      "smart_night_mode_select": {
        "name": "Smart night mode"
      }
    },
    "switch": {
      "clock_enabled": {
        "name": "Clock"
      },
      "shuffle": {
        "name": "Shuffle photos"
      },
      "clock_backdrop": {
        "name": "Clock backdrop"
      },
      "favorites_only": {
        "name": "Favorites only"
      },
      "adaptive_readability": {
        "name": "Adaptive readability"
      },
      "burn_in_protection": {
        "name": "Burn-in protection"
      },
      "smooth_transitions": {
        "name": "Smooth transitions"
      },
      "smart_day_mode": {
        "name": "Smart day mode"
      },
      "self_healing": {
        "name": "Kiosk self-healing"
      },
      "page_error_fallback": {
        "name": "Page error fallback"
      }
    },
    "text": {
      "message_text": {
        "name": "Send message"
      },
      "smart_morning_start": {
        "name": "Smart morning start"
      },
      "smart_day_start": {
        "name": "Smart day start"
      },
      "smart_evening_start": {
        "name": "Smart evening start"
      },
      "smart_night_start": {
        "name": "Smart night start"
      }
    },
    "update": {
      "software_update": {
        "name": "Software update"
      }
    }
  }
}
