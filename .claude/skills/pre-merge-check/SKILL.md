---
name: pre-merge-check
description: Final gate before opening or merging a SpartanPort PR. Use when asked "is this ready", "can we merge", "open the PR", or right before a merge.
---

# Pre-merge check

Run each check and report pass, fail or not run, with evidence. Any unchecked item blocks the merge.

1. **Diff is only the intended change.** `git diff origin/main...HEAD --stat`. No debug output, no unrelated reformatting, no files from `out/`, `user/`, dumps or logs.
2. **No game data.** Nothing matching `eboot.bin`, `*.sprx`, `*.self`, `*.pkg`, `*.elf`, `sce_sys/`, `sce_module/`; no keys; no long proprietary decompilation.
3. **Tests.** Python suite output pasted, no new failure versus the Windows baseline in `CLAUDE.md`. Native tests built and run on at least one platform, the other named as unchecked. Skipped tests reported as unchecked.
4. **Guest-context ISA.** If `src/*_hook.h` or `isa_*` changed: `tests/test_hook_isa.py` ran with `iced-x86` installed.
5. **Reviewer pass done** on the full diff. High-risk change (hook or patch sites, ISA rewrite, loader and memory code, startup path, updater, settings or save migration, GPU synchronization): the user was asked about a second independent reviewer.
6. **Every WARN has a disposition** (issue filed, fixed, or dismissed with a reason). Every actionable review thread is resolved.
7. **Docs match.** README x3, `docs/PATCHES*.md`, `docs/MODS*.md` updated, or the untranslated files named. Launcher strings added through `spartanport_lang.py`.
8. **Real run.** The change was exercised in the actual port where possible (log line for a patch, launcher page opened, game started on the stated GPU). If it could not be, the PR says exactly what was not checked: platform, CPU class, GPU vendor, game build.
9. **Hygiene.** Commit subjects are `Type(Scope): past-tense summary (#issue)`; no AI or tool attribution; no em dashes; no version bump or workflow release change unless this is the release PR.
10. **PR text.** Short title in the same format, body with what changed, why, how it was tested and what was not. `Refs #n` / `Fixes #n`. Target repo `FelipePrado0/SpartanPort`, from the fork with `--head Gaarasu:<branch> --base spartanport`. PRs never target `main`.
11. **CI.** The workflows here are manual. If the change touches packaging, `build.sh`, or dependencies, a `workflow_dispatch` build on the branch (no tag) passed, or you say it was not run.

Merge method is the maintainer's. Do not merge on the user's behalf unless asked.
