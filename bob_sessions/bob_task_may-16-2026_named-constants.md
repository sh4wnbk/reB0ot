# Bob Task - Named Constants

Date: 2026-05-16

## Task
Replace all hard-coded truncation numbers with named constants in reboot.py

## Changes Made

1. Added named constants after credential patterns (lines 82-86):
   - HEAD_CHARS = 800
   - MIDDLE_CHARS = 400
   - TAIL_CHARS = 1800
   - MAX_EXPORT_CHARS = HEAD_CHARS + MIDDLE_CHARS + TAIL_CHARS

2. Replaced all hard-coded numbers in generate_restoration_string():
   - Line 137: Changed `3000` to `MAX_EXPORT_CHARS`
   - Line 138: Changed `800` to `HEAD_CHARS`
   - Line 139: Changed `-1800` to `-TAIL_CHARS`
   - Line 142: Changed `800` to `HEAD_CHARS`
   - Line 143: Changed `1800` to `TAIL_CHARS`
   - Line 162: Changed `400` to `MIDDLE_CHARS`
   - Line 165: Changed `400` to `MIDDLE_CHARS`
   - Line 166: Changed `400` to `MIDDLE_CHARS`
   - Updated comment on line 136 to reference constant names

## Benefits
- Improved code maintainability
- Single source of truth for truncation values
- Self-documenting code with meaningful constant names
- Easier to adjust truncation strategy in the future

## Status
Completed successfully. All hard-coded truncation numbers replaced with named constants.