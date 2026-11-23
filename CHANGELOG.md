# Changelog

## 0.1.0 — 2026-11-23

- Initial standalone release for **SILENT HILL 2 Remake (Steam, PC)**.
- Local read-only UE5 IoStore/Pak extractor for all 41 paper map sheets (`2048×2048`), 48 red-marker sprites, high-res inventory & Polaroid renders (up to `768 px`), localized room/street labels, and `RU`/`EN` item names, descriptions, save-point titles, and full transcripts (including memos, Strange Photo captions, and Mary's Letter).
- Factory-exact `World (X, Y) → Pixel` projection from `USHGameplayMapBaseWidget` anchors & rotations across all 41 maps.
- Byte-exact `VASb` + `GVAS` + `UcaSave` save reader (`SaveGameData_*.sav` & `UcaSave.sav`) tracking Memos, Strange Photos, Glimpses of the Past, Keys, Weapons, `MapsObjectsData` red-pen marks, pushable carts, and active-chapter world pickups.
- Persistent read-only `PROCESS_VM_READ` (`0x0410`) live UE 5.1 telemetry for `SHProto-Win64-Shipping.exe` (build `1.0.0.5`) with 15 Hz SSE stream, 60 FPS interpolated James tracking, optional breadcrumb trail, and automatic floor/world switching via `ASHGameplayMapVolume`.
- Full-screen tablet & desktop companion suite (`Map` / `Loadout` / `Archive` / `Safes & Codes`) with Fog/Otherworld theme shift, always-visible animated clinical ECG pulse HUD, unified Large Inspect Lightbox (Polaroids, Memos, Personal Mementos, Pocket Clues), Anti-Spoiler mode, USB ADB (`tablet_usb.bat`), LAN Wi-Fi, PWA manifest, and optional Windows logon autostart (`install_autostart.ps1`).
