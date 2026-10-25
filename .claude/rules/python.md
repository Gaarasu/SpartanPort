---
paths:
  - "launcher/**"
  - "scripts/**"
  - "run.py"
  - "tools/**/*.py"
---

# Python rules (launcher, preparation, tools)

- Target Python 3.10 or newer (the README says 3.10; Windows packaging builds with 3.13). Do not use syntax or stdlib added after 3.10 without checking. `python -I -m py_compile` is not enough: run the unit tests.
- Third-party packages are `pillow`, `iced-x86==1.21.0` and (tools only) `capstone`. A new dependency is pinned to an exact version, justified, and added to the Windows and Linux packaging steps. The launcher must start without optional packages and degrade, the way `isa_rewrite.iced_x86` does.
- Cross-platform: `pathlib`, no hard-coded `\` or drive letters, no POSIX-only calls without a guard. Windows-only code is guarded by `sys.platform`.
- The launcher is Tk. UI code must not block the event loop on I/O or subprocesses; follow how the existing pages use threads and `after`.
- User-visible text goes through `launcher/spartanport_lang.py` (`KEYS` holds the English text, each language lists its texts in the same order; Russian sits in `spartanport_launcher_win.py`). Add a key, then add it to every language list or accept the English fallback and say so. Never concatenate translated fragments.
- Settings and user data: keep reading old files. `gow3.ini` and the old launcher settings are migrated on first start; a saved `spartanport.ini` resolution wins over auto-detected defaults. Writes are atomic enough not to corrupt on a crash.
- Anything that reads a zip, a mod, a save or a downloaded update rejects absolute paths, `..` and symlinks, and checks hashes where the updater already does. A subprocess gets an argument list, never a shell string built from user data.
- `scripts/` is the glue that runs at game start (`prepare.py`, `patches.py`, `isa_rewrite.py`). Its log lines are quoted in the docs. Do not reword them casually.
- Write the test first. Tests import sibling modules through `tests/paths.py`.
