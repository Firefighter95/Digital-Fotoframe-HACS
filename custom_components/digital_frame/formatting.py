from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.util import dt as dt_util


def format_duration(value: Any) -> str | None:
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return None

    seconds = max(0, seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def format_timestamp(value: Any) -> str | None:
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    return dt_util.as_local(parsed).strftime("%d-%m-%Y %H:%M:%S")

