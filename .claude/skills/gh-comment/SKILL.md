---
name: gh-comment
description: Post a comment, review, or close note on a SpartanPort GitHub issue or PR. Use for every comment sent to GitHub; the project requires English first, then Brazilian Portuguese.
---

# GitHub comments (bilingual)

Source of truth: `docs/agents/issue-tracker.md`. Every comment on an issue or PR goes in English first, then Brazilian Portuguese, with the same content. This holds even when the other person writes only English. A PreToolUse hook blocks `gh issue|pr comment|review|close --comment` without both markers, and any `gh issue|pr` call without `-R`.

## Format

Exactly one `---`, between the languages, none inside either section:

```
**EN:**

<text>

---

**PT-BR:**

<same text translated>
```

## Steps

1. Run the `no-ai-slop` skill on the English text. Short, specific, no em dashes, no AI or tool attribution.
2. Translate the whole thing. Keep code, commands, file paths, error text and issue numbers identical in both. Do not summarize in one language.
3. Put the body in a file (a temp file outside the repo) and post with `--body-file`, so quoting cannot mangle it:
   ```bash
   gh issue comment <n> -R FelipePrado0/SpartanPort --body-file <file>
   gh pr comment <n> -R FelipePrado0/SpartanPort --body-file <file>
   gh issue close <n> -R FelipePrado0/SpartanPort --comment "$(cat <file>)"
   ```
4. If a comment already went out in one language only, edit it in place instead of posting a second one:
   ```bash
   gh api -X PATCH repos/FelipePrado0/SpartanPort/issues/comments/<id> -F body=@<file>
   ```
5. `gh` needs `gh auth login` first. If it is not authenticated, stop and say so.

## Content

- A reply to a bug report asks for what is missing from the template (port version, GPU and driver, CPU, `user/last_run.log`) or states what was found and what is next. Say which build and hardware a finding applies to.
- A fix note names the commit or PR, the version it ships in if known, and what the reporter should check. The `awaiting-confirmation` label means "fix shipped, waiting for the reporter"; it is closed after 7 days without a reply (`docs/agents/triage-labels.md`).
- Never paste game data, keys or long decompiled code into an issue.
