# TODO: Fix Hash Check and Translation Issues

## Tasks
- [x] Lower sensitivity in screen_capture.py from 0.85 to 0.5 to reduce false positives in change detection.
- [x] Change _debounce_scans in main.py from 2 to 0 for immediate translation after text stability.
- [x] Add min_interval=0.3 and implement time-based debounce in main.py to prevent translations more frequent than 0.3 seconds per region.
- [x] Remove debounce logic and translate immediately after OCR results.
- [ ] Test the application to ensure scans are less frequent and translations occur immediately after changes.

## Notes
- Sensitivity affects RegionWatcher thresholds for detecting changes.
- Debounce ensures text stability before translating.
- Min interval adds a time buffer between translations to avoid spam.
