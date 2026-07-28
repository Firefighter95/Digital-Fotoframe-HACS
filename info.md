# Digital Frame

Local Home Assistant integration for the LAN Digital Frame server.

It adds notify, button, switch, select, number, binary sensor, sensor, image, text and update entities for controlling the frame from Home Assistant. It can send priority messages, sync a Home Assistant weather entity to the clock, show an admin QR code, apply smart day mode, control fullscreen/reload/photo navigation, expose PC health, fire automation-friendly events, export redacted diagnostics, apply an uploaded update and restart the kiosk browser or mini PC.

Repository root must contain `custom_components/digital_frame/manifest.json`. Do not put the integration inside an extra parent folder.
