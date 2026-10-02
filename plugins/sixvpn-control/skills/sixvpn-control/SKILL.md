---
name: sixvpn-control
description: Check 6VPN status and schedules, preview ordinary schedule changes, and apply a change only after the user explicitly approves the preview.
---

Use `sixvpn_status` before other app operations. If the app is not running, tell the user to open it.

For a web schedule change, call `sixvpn_preview_schedule` first and explain the returned interpretation in plain Korean. Do not call `sixvpn_apply_schedule` in the same turn as the preview. Wait until the user explicitly asks to apply the reviewed change, then call apply with the same command and `confirm: true`.

For a game or Windows app, require both its display name and exact `.exe` filename. Do not guess an executable when uncertain. Call `sixvpn_preview_app_block`, then tell the user that it creates an every-day, all-day block and may close the app while the schedule is active. Wait for a separate, explicit apply request before calling `sixvpn_apply_app_block` with the returned preview ID. Previews expire after five minutes. If 6VPN protection is paused, do not enable it; the app rejects the apply request.

Never use this plugin to stop or close a browser, enable or disable protection/enforcement, lock the computer, temporarily allow blocked sites, delete or merge schedules, or run shell commands. Use the 6VPN app for those actions.
