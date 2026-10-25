---
paths:
  - "src/**"
  - "gpu/shim/**"
---

# Native code rules (loader, runtime, shim)

`src/` is C11. `gpu/shim/` is C++23. Both build on clang (MSYS2 CLANG64, Windows) and GCC 14 (Ubuntu 24.04).

## Build flags and headers

- `-Wall -Wextra -Werror` everywhere. Do not silence a warning with a pragma to get a build through; fix the cause. Third-party decoders (LibAtrac9) are the only code built without `-Werror`.
- New files start with `/* SPDX-License-Identifier: GPL-2.0-or-later */`. Header guards are `SPARTAN_<NAME>_H`.
- No `-march=` flags: the same binary runs on a Steam Deck and on a Sandy Bridge desktop.
- Windows-only API goes through `compat_win.c/h` or an `#ifdef _WIN32` block. A change that compiles on one platform only is not done: name the other platform as unchecked.

## Code that runs in the guest's context

The ISA rewrite (`isa_rewrite.c`, `isa_emulate.c`) patches only the game's own code. Everything else that executes on the host as written must run on the oldest supported CPU (Intel Sandy Bridge, AMD FX):

- Hook stubs in `src/*_hook.h` and ISA-rewrite stubs: no BMI1, BMI2, LZCNT, MOVBE, F16C, AVX2, FMA. Typical offenders are `andn`, `blsr`, `bextr`, `tzcnt`, `lzcnt`, `movbe`. `tests/test_hook_isa.py` decodes the byte arrays and fails on them (it needs `iced-x86`). #818 was exactly this.
- `isa_emulate.c` builds with `-mgeneral-regs-only` and calls nothing from libc, not even `memcpy`. It runs inside guest code with no XMM/YMM state saved.
- Functions called from guest code use the `ABI` macro (`__attribute__((sysv_abi))`, `src/runtime.h`). A missing `ABI` on Windows silently uses the wrong calling convention.

## Runtime and loader

- `runtime_*.c` reimplements PS4 system functions. Match the PS4 return codes and the argument semantics the game relies on. Cite how you know (a disassembly address, the log of a failing call), not what you remember of the SDK.
- A fatal startup condition prints one `STOP: <reason>` line and exits with code 20. Log text that tools and docs quote (`CPU:`, `ISA:`, `Patches:`, `STOP:`) is an interface: changing the wording needs `docs/PATCHES*.md` and the launcher's log parsing checked.
- Check every return value of allocation, mapping and file calls. Bound every copy of data that came from the game, a save file or a mod.
- Shared state across threads (the GPU, recording, preparation and copy threads, the audio threads) needs a stated owner and lock. Say which thread a function runs on in a comment when it is not obvious.
- Hot paths (per frame, per draw, per guest call) get no new allocation, syscall or lock without a measurement in the commit message.

## Hooks and signatures

Follow `.claude/rules/patches-and-signatures.md` for anything that finds a site in the game image.
