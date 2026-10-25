---
paths:
  - "patches/**"
  - "scripts/patches.py"
  - "tools/make_signatures.py"
  - "src/*_hook.h"
  - "src/signature.h"
  - "docs/PATCHES*.md"
---

# Patches, hooks and signatures

Use the `signature-site` skill to add or move a site. Facts to hold on to:

- Fixed addresses in `Address=` and in `src/*_hook.h` belong to one particular `eboot.bin` (the tools call it the reference). The full 01.02 update (sha256 `6e72330e...`, the user's dump) has shifted code (cheat, actor, damage and orb sites are 0x10 earlier than their hints), so those addresses differ there. PS4 virtual addresses use base `0x400000`. Always hash the eboot you analyze. A fixed address is valid only for one build; it is a hint, never the lookup key.
- A site is found by `Pattern` (hex bytes, `??` for bytes another build may change: rip-relative displacements and rel32 branch/call targets) and `At` (offset of the write inside the pattern). The pattern must match exactly once in the image. Written bytes stay fixed, so a match also proves the original bytes are there.
- `tools/make_signatures.py EBOOT ADDR:LEN ...` produces the shortest unique window, with a 16-byte minimum so a chance match in another build stays unlikely. Do not hand-write a pattern when the tool can write it.
- XML patches (`patches/CUSA01623.xml`, shadPS4/GoldHEN format) apply only when all of a patch's sites are found. Otherwise the patch is left out whole and the log says why. C hooks (`SpartanSignature` in `src/signature.h`) behave the same: a missing site turns off that hook only.
- Never make a missing site fatal. Never fall back to the fixed address when the signature fails: that writes into the wrong code on another build.
- Hook stub bytes obey the oldest-CPU rule (no BMI1/BMI2/LZCNT/MOVBE/F16C/AVX2/FMA). Run `tests/test_hook_isa.py` with `iced-x86` installed; skipped means unchecked.
- Credit the patch author in `Author=` and in the docs table when the idea or bytes come from someone else (cuesta4, kvicken, Celogamez are already credited that way). Check licenses before copying bytes from another project.
- Every new hook or patch gets a test for the found case and for the not-found case, using the data in `tests/data/` (`eboot_6e72_sites.json` holds sites for a second build) or a synthetic buffer like `tests/test_signatures.cpp`. A test that needs the user's dump must say so and skip cleanly without it.
- `*.patch` files are LF-only (`.gitattributes`). Do not let an editor convert them.
- Update `docs/PATCHES.md`, `.es.md` and `.pt-BR.md` when the built-in patch table or the log lines change.
