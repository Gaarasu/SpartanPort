---
paths:
  - "README*.md"
  - "docs/**"
  - "launcher/spartanport_lang.py"
---

# Docs and translations

- User-facing docs come in triplets: `X.md`, `X.es.md`, `X.pt-BR.md` (README, MODS, PATCHES). When behavior users see changes, update all three in the same commit. If you cannot translate with confidence, update English, keep the structure identical in the others, and say in the report which files still need translation. Do not leave a translated file describing the old behavior without a note.
- Tables, headings and anchors keep the same structure across the three languages so links keep working.
- Docs state current facts. Do not narrate how a bug was found or how review went.
- Do not paste game text, copyrighted art or unlicensed screenshots. Screenshots must not show personal paths or names; `docs/images/*.png` is the only tracked PNG location for docs.
- Technical claims about the game (addresses, behavior, supported builds) name the build they were observed on.
- `docs/plans/` and `docs/specs/` hold dated design and plan files (`YYYY-MM-DD-<slug>.md`, `YYYY-MM-DD-<slug>-design.md`). Existing ones are partly in Portuguese; write new ones in English unless the user says otherwise.
- `docs/agents/` configures the issue tracker and triage labels for agent skills. Do not rewrite it as a side effect of another change.
- Credits: when you take an idea, bytes or code from someone, add them to the Credits section of the README (all three) and to the relevant doc table.
- Writing style: run the `no-ai-slop` skill. Plain, specific, no em dashes.
