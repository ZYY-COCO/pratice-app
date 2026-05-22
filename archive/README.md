# Archive

This folder keeps non-runtime project artifacts out of the production source path.

- `temp_extraction/`: local extraction leftovers and downloaded fragments. These files are ignored by Git.
- `dangerous_sql/`: manual-only SQL that can reset or delete production data. SQL files in this folder are ignored by Git on purpose.

Do not run anything under `dangerous_sql/` unless you are intentionally resetting or deleting live data and have a backup.
