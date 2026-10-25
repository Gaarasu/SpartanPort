---
name: signature-site
description: Add, move or verify a patch or hook site in the God of War III image by byte signature. Use when adding an XML patch line, a C hook in src/*_hook.h, when a site stops matching on another build, or when asked for a signature.
---

# Signature site

A site is identified by the original bytes around it, not by address. The address only labels the reference build. Background: `docs/PATCHES.md` ("Writing a patch"), `src/signature.h`, `tools/make_signatures.py`.

## Steps

1. **Pin the build.** Record the `eboot.bin` sha256 and the image (eboot, libc, libSceFios2). Addresses are PS4 vaddrs with base `0x400000`. The offsets already in `src/*_hook.h` and `Address=` in the XML belong to one particular eboot (the "reference" in the tool docs); the full 01.02 update (sha256 `6e72330e...`) differs: measured on 2026-10-21, the cheat, actor, damage and orb sites sit 0x10 bytes earlier than their header hints, while the QTE sites match theirs. That is exactly why signatures exist. (The +0x120 / -0x10 in `tests/test_signatures.cpp` is a synthetic test layout, not this build.) Do not assume which build you have: hash it.
2. **Know what you write.** Address, how many bytes are overwritten, the original bytes, the replacement. Overwrite whole instructions only. If the replacement is longer than the site, move the original instructions into a hook stub and jump (see `src/cheat_hook.h` for the pattern: `original`, `replacement`, `site`).
3. **Generate the signature, do not hand-write it** (needs `pip install capstone`; run on the prepared or original eboot):
   ```bash
   python tools/make_signatures.py path/to/eboot.bin 0xADDR:LEN [0xADDR2:LEN ...]
   python tools/make_signatures.py path/to/eboot.bin 0xADDR:LEN:data      # constant data, no disassembly
   python tools/make_signatures.py path/to/eboot.bin 0xCALLSITE --ref 0xCALLSITE   # a Target: prints Pattern, Ref, Tail
   ```
   The tool returns the shortest window (16 bytes minimum) that occurs exactly once, with `??` on rip-relative displacements and rel32 branch targets. If it cannot find a unique window, the site is ambiguous: pick a neighboring instruction or report it, do not shorten the pattern by hand.
4. **Check the other build.** Run the same pattern against CUSA01715 / 01.00 if the dump is available (`scripts/patches.py` `find_pattern`), or against `tests/data/eboot_6e72_sites.json`. A signature that is unique here and absent there is fine only if absence is the correct, logged outcome.
5. **Write it down.**
   - XML: `<Line Type="bytes" Address="0x..." Value="..." Pattern="aa bb ?? ?? ?? ?? cc" At="N"/>` in `patches/CUSA01623.xml`. `At` counts bytes from the start of `Pattern`.
   - C hook: `SpartanSignature site = {"aa bb ?? ?? ?? ?? cc", at}` next to the original and replacement bytes, with the offset as the reference-build hint.
6. **ISA check.** The replacement and any stub must not use BMI1, BMI2, LZCNT, MOVBE, F16C, AVX2 or FMA. Run `python -m unittest discover -s tests -p "test_hook_isa.py"` with `iced-x86==1.21.0` installed. If it is skipped, say the ISA check did not run.
7. **Not-found behavior.** Remove the fixed-address fallback if there is one. The patch or hook is left out whole, the log says which and why, and the game starts.
8. **Tests.** Found, not found, found twice, found at a shifted offset. C hooks: extend `tests/test_signatures.cpp` (with a prepared `out/eboot.elf` the test also checks the real sites). Python side: `tests/test_patches*.py`-style tests using synthetic images.
9. **Docs.** `docs/PATCHES.md` + `.es.md` + `.pt-BR.md` table and credits if the patch is new or its source is someone else's work.
10. **Verify in the log.** After starting the game with the change, `user/last_run.log` must list the patch in the `writes from [...]` line and not in a `skipped` line. If you cannot run the game, say so.

## Report

Give the user: build and sha256, address and length, original and replacement bytes, the signature, uniqueness result per build, ISA result, and what was not verified.
