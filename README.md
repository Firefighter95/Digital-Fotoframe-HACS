# Digital Frame for Home Assistant

HACS custom integration for the local LAN Digital Frame. It talks directly to the frame server on the mini PC. This integration expects frame server `V 2.2.0` or newer.

## Features

- UI configuration through Home Assistant.
- Device in Devices & services.
- Notify entity for `notify.send_message`.
- Screen on/off, clock, shuffle, clock backdrop, favorites-only, adaptive readability, burn-in protection, smooth transitions, smart day mode, self-healing and page-error fallback switches.
- Selects for mode, editable mode list, photo selection, saved page, weather entity, clock position, photo fit, F1 provider and smart day/evening/night target modes; the mode list and saved pages refresh every 5 seconds.
- Number entities for slideshow interval, photo dark overlay, clock size, clock backdrop opacity and web-page fallback timing.
- Button entities for reload, fullscreen, next/previous photo, identify, admin QR, apply smart mode, kiosk restart, PC power actions and applying an uploaded update.
- Binary sensors for display connection, kiosk browser connection, fullscreen and problem state.
- Sensors for version, mode, screen status, current photo, current URL, update status, latest upload, display health and mini PC health.
- Uptime sensors are shown as readable durations, and date fields are shown as local date/time strings.
- Optional weather entity sync: choose a `weather.*` entity in the integration options or the `Weather entity` select, and the frame shows temperature, condition, humidity and wind next to the clock.
- Status image entity with a lightweight current-view summary.
- Text entities for sending a quick message and editing smart day-mode start times.
- Services to show mode-list items, send priority messages, URLs, save/show/delete pages, show the admin QR, apply smart mode, reload/fullscreen the display, control photos, restart the kiosk browser, apply an uploaded update, restart/shutdown the mini PC and turn the screen on/off.
- Home Assistant events for mode changes, photo changes, update status changes and problem changes.
- Diagnostics export with PIN, host and URL fields redacted.

## HACS installation

1. Extract `digital-frame-home-assistant-hacs.zip`.
2. Put the extracted contents in the root of your GitHub repository. Do not put the zip itself in `main` as the only file and do not keep an extra parent folder around it.
3. Check that the GitHub root shows this structure:

```text
custom_components/
  digital_frame/
    manifest.json
README.md
hacs.json
info.md
```

4. Open HACS > Custom repositories.
5. Add the repository URL with type `Integration`.
6. Install `Digital Frame`.
7. Restart Home Assistant.
8. Go to Settings > Devices & services > Add integration.
9. Search for `Digital Frame`.
10. Fill in:
   - Host: the IP address or hostname of the mini PC
   - Port: `8787`
   - PIN: the admin PIN of the photo frame
   - Actor: `Home Assistant`
11. Optional: open the integration options/Configure screen or use the `Weather entity` select and choose a `weather.*` entity. The integration pushes that weather data to the frame every time it changes.

When publishing, update `documentation` and `issue_tracker` in `custom_components/digital_frame/manifest.json` to your own repository.

If HACS shows `Repository structure for main is not compliant`, the repository root is wrong or only the zip was uploaded to the branch. Move `custom_components`, `README.md`, `hacs.json` and `info.md` to the top level of the `main` branch. Do not upload `digital-frame-home-assistant-hacs.zip` as a file inside `main`.

## Manual testing

1. Extract `digital-frame-home-assistant-hacs.zip`.
2. Copy `custom_components/digital_frame` to `/config/custom_components/digital_frame`.
3. Restart Home Assistant.
4. Add the integration through Settings > Devices & services.

In the frame admin portal, give the name `Home Assistant` at least the `Display control` permission. For configuration entities such as clock/overlay/slideshow settings, give it `Change settings`. For PC health sensors and PC power buttons/services, give it `Manage PC`. For the update entity and apply-update button/service, give it `Manage updates`.

## Entities

- `switch.*_screen`: screen on/off.
- Other switches: clock, shuffle, clock backdrop, favorites-only, adaptive readability, burn-in protection, smooth transitions, smart day mode, self-healing and page-error fallback.
- `select.*_mode`: photos, web page, F1, message, meters, admin QR or blank screen.
- `select.*_photo_selection`: all visible photos or favorites only.
- `select.*_mode_list`: the editable button list from the frame admin portal.
- `select.*_page`: saved pages from the admin portal.
- Other selects: weather entity, clock position, photo fit, F1 provider and smart target modes.
- Numbers: slideshow interval, photo dark overlay, clock size, clock backdrop opacity and page fallback seconds.
- Buttons: reload display, force fullscreen, next/previous photo, identify, show admin QR, apply smart mode, restart kiosk browser, PC restart/shutdown/cancel and apply uploaded update.
- Binary sensors: display connected, kiosk browser connected, browser fullscreen and problem.
- Update entity: apply an update package after it has been uploaded through the frame admin portal.
- Image entity: lightweight status image for dashboard cards.
- Notify entity: use Home Assistant's `notify.send_message` action.
- `text.*_send_message`: type a message and save it to show it on the frame for 60 seconds.
- Smart start text entities: edit the `HH:MM` start time for morning, day, evening and night slots.
- Sensors for version, mode, screen status, photo count, active page, current photo, current URL, browser status, update status, latest upload, smart slot, self-healing last action and last error.
- Display-health sensors: uptime, slide nodes and JS heap used.
- PC sensors: status, uptime, CPU usage, memory usage, disk usage, process memory and network address.
- Weather entity select: choose which Home Assistant `weather.*` entity is synced to the photo frame clock, or select `Off`.
- Events: `digital_frame_mode_changed`, `digital_frame_photo_changed`, `digital_frame_update_status_changed` and `digital_frame_problem_changed`.
- Diagnostics: Home Assistant can download redacted integration diagnostics from the device/integration page.

## Services

Use these in automations, for example:

```yaml
service: digital_frame.send_message
data:
  title: Doorbell
  message: Someone is at the front door.
  duration: 30
  priority: high
```

```yaml
service: digital_frame.show_page
data:
  page_id: home-assistant
```

```yaml
service: digital_frame.show_mode_item
data:
  mode_item_id: home-assistant
```

```yaml
service: digital_frame.save_page
data:
  page_id: weather
  name: Weather
  url: https://example.com/dashboard
```

```yaml
service: digital_frame.delete_page
data:
  page_id: weather
```

```yaml
service: digital_frame.show_message
data:
  title: Laundry is ready
  message: Please empty it.
  duration: 60
```

`digital_frame.show_message` remains available for older automations. New automations can use `digital_frame.send_message`.

```yaml
service: digital_frame.show_url
data:
  url: https://globe.adsbexchange.com/
```

```yaml
service: digital_frame.screen_off
```

```yaml
service: digital_frame.force_fullscreen
```

```yaml
service: digital_frame.next_photo
```

```yaml
service: digital_frame.restart_kiosk
```

```yaml
service: digital_frame.show_admin_qr
```

```yaml
service: digital_frame.apply_smart_mode
```

```yaml
service: digital_frame.restart_pc
```

You can also use Home Assistant's native notify action:

```yaml
service: notify.send_message
target:
  entity_id: notify.digital_frame_notify
data:
  message: Someone is at the front door.
  data:
    priority: high
    duration: 30
```

Example automation:

```yaml
alias: Restart photo frame PC on high memory
trigger:
  - platform: numeric_state
    entity_id: sensor.digital_frame_pc_memory_usage
    above: 95
    for: "00:10:00"
action:
  - service: digital_frame.restart_pc
mode: single
```

Example fullscreen watchdog:

```yaml
alias: Keep photo frame fullscreen
trigger:
  - platform: state
    entity_id: binary_sensor.digital_frame_browser_fullscreen
    to: "off"
    for: "00:00:20"
action:
  - service: digital_frame.force_fullscreen
mode: single
```

Example problem event:

```yaml
alias: Photo frame problem alert
trigger:
  - platform: event
    event_type: digital_frame_problem_changed
    event_data:
      active: true
action:
  - service: notify.mobile_app_phone
    data:
      message: "The photo frame reports a problem."
mode: single
```
