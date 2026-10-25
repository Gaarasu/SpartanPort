---
paths:
  - "tests/**"
---

# Testing rules

Three kinds of tests live here:

| Kind | Files | Run |
|---|---|---|
| Python `unittest` | `tests/test_*.py` | `python -m unittest discover -s tests -p "test_*.py"` |
| C runtime tests | `tests/test_*.c` | `bash build.sh --test` (Linux), or the `*-test` Ninja targets in `gpu/CMakeLists.txt` (Windows) |
| C++ GPU and hook tests | `tests/test_*.cpp` | `ninja -C out/gpu <name>-test`, then run `out/gpu/<name>-test` |

## Rules

- Test one behavior per test. Name it for the behavior (`test_mod_symlinks_rejected`), not the function.
- A bug fix gets a regression test. Prove a new test can fail: break the code under test, watch it fail for the right reason, restore it.
- Tests must not need the user's game dump. If one genuinely does (`--check-imports`, `stat-multipliers-test out/eboot.elf`), it takes the path as an argument or env var and skips or exits cleanly without it. Never commit game bytes to make a test pass: use a synthetic buffer, or the small fixtures in `tests/data/`.
- Optional dependencies skip with a reason: `@unittest.skipUnless(isa_rewrite.iced_x86, 'pip install iced-x86')`. A skipped test is unchecked, not passed. Say so in the report.
- Platform-specific tests are guarded (`sys.platform`), like the existing Tk, Windows named pipe and Linux permission tests.
- No absolute machine paths. Use `tests/paths.py` (`ROOT`) and `tempfile`/`tmp` directories. Fake paths such as `/home/user/...` are fine as inert strings.
- Do not touch the real user folder, the real registry or the network. Mock the Discord pipe, the updater and `subprocess`.
- Mock the external boundary, not the logic under test.
- Test files stay focused. Split by concern when one grows past a few hundred lines.

## Baseline

On Windows a clean checkout has known failures: `test_glyphs.GlyphPatchTest` (12), `test_discord_presence.GameProcessPresence` (3), `test_mods.ModTests.test_mod_symlinks_rejected`. Report new failures against that list. Do not edit those tests to turn the run green unless the task is to fix them.
