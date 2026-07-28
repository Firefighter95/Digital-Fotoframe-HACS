# Digital Frame for Home Assistant

HACS custom integration for the local LAN Digital Frame. It talks directly to the frame server on the mini PC. Basic controls expect server `V 1.7.0` or newer; the editable mode-list selector expects server `V 1.10.0` or newer; PC sensors and restart service expect server `V 1.11.0` or newer.

## Features

- UI configuration through Home Assistant.
- Device in Devices & services.
- Screen on/off switch.
- Selects for mode, editable mode list, photo selection and saved page; the mode list and saved pages refresh every 5 seconds.
- Sensors for version, mode, screen status, photos, active page and mini PC health.
- Text entity for sending a quick message from Home Assistant to the screen.
- Services to show mode-list items, send messages, URLs, save/show/delete pages, restart the mini PC and turn the screen on/off.

## HACS installation

1. Extract `digital-frame-home-assistant-hacs.zip`.
2. Put the extracted contents in the root of your GitHub repository. Do not commit the zip file itself and do not keep an extra parent folder around it.
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

When publishing, update `documentation` and `issue_tracker` in `custom_components/digital_frame/manifest.json` to your own repository.

If HACS shows `Repository structure for main is not compliant`, the repository root is wrong. Move `custom_components`, `README.md`, `hacs.json` and `info.md` to the top level of the `main` branch and remove any wrapping folder such as `digital-frame-home-assistant`.

## Manual testing

1. Extract `digital-frame-home-assistant-hacs.zip`.
2. Copy `custom_components/digital_frame` to `/config/custom_components/digital_frame`.
3. Restart Home Assistant.
4. Add the integration through Settings > Devices & services.

In the frame admin portal, give the name `Home Assistant` at least the `Display control` permission. For PC health sensors and `digital_frame.restart_pc`, also give it `Manage PC`.

## Entities

- `switch.*_screen`: screen on/off.
- `select.*_mode`: photos, web page, F1, message, meters or blank screen.
- `select.*_photo_selection`: all visible photos or favorites only.
- `select.*_mode_list`: the editable button list from the frame admin portal.
- `select.*_page`: saved pages from the admin portal.
- `text.*_send_message`: type a message and save it to show it on the frame for 60 seconds.
- Sensors for version, mode, screen status, photo count and active page.
- PC sensors: status, uptime, CPU usage, memory usage, disk usage, process memory and network address.

## Services

Use these in automations, for example:

```yaml
service: digital_frame.send_message
data:
  title: Doorbell
  message: Someone is at the front door.
  duration: 30
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
service: digital_frame.restart_pc
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
