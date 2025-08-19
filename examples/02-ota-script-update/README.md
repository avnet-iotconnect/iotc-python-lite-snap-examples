# 02 – OTA Script Update (guide)

This guide walks through updating a local script delivered via IoTConnect OTA.

1. Package your script and assets into a `.tar.gz`.
2. Deliver to the device using IoTConnect OTA targeting the `iotconnect` snap context.
3. Install to `$SNAP_COMMON/ota/<package>/` and restart your app.
4. Your app should read models/scripts from `$SNAP_COMMON` so OTA replacements take effect.

> Tip: Keep writeable state in `$SNAP_COMMON` and treat the snap itself as read-only.