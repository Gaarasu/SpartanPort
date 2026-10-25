#!/usr/bin/env python3
"""PreToolUse hook for Bash and PowerShell: enforces the commit, push and gh rules in CLAUDE.md.

Reads the hook JSON on stdin. Exit 2 with a reason on stderr blocks the call; exit 0 allows it.
Written in Python (not shell + jq) so it runs the same on Windows and Linux.
"""
import json
import os
import re
import subprocess
import sys

UPSTREAM = 'FelipePrado0/SpartanPort'
EM_DASH = '—'
SUBJECT = re.compile(r'^(Feat|Fix|Docs|Chore|Refactor|Test|Perf|Build|CI|Style|Revert)\([A-Za-z0-9 _/.+-]+\): \S')
ATTRIBUTION = re.compile(r'co-authored-by:|noreply@anthropic|generated with \[?claude|\U0001F916|claude\.ai/code', re.I)
# Game data must never be committed: the project ships no game files.
GAME_FILES = re.compile(r'(^|/)(eboot\.bin|param\.sfo|[^/]+\.(sprx|self|pkg|elf|psarc))$|(^|/)(sce_sys|sce_module)/', re.I)
LEAD = r'(?:^|[;&|(]\s*)(?:\w+=\S+\s+)*(?:(?:sudo|env|time|command|nohup)\s+)*'
GIT = LEAD + r'git(?:\s+-[cC]\s+\S+)*\s+'
BILINGUAL_HELP = (
    'GitHub comments go in English first, then Brazilian Portuguese, same content, one `---` between:\n'
    '**EN:**\n\n<text>\n\n---\n\n**PT-BR:**\n\n<same text translated>\n'
    '(docs/agents/issue-tracker.md, "Comments are bilingual")')


def block(*reasons):
    sys.stderr.write('Blocked by project CLAUDE.md rules:\n' + '\n'.join('- ' + r for r in reasons) + '\n')
    sys.exit(2)


def git(repo, *args):
    try:
        done = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=15)
    except (OSError, subprocess.SubprocessError):
        return ''
    return done.stdout.strip() if done.returncode == 0 else ''


def head_of(cmd):
    """The command without heredoc / here-string bodies, so message text is not parsed as commands."""
    cut = [m.start() for m in (re.search(r'<<', cmd), re.search(r"@['\"]\s*$", cmd, re.M)) if m]
    return cmd[:min(cut)] if cut else cmd


def repo_dir(cmd, cwd):
    m = re.search(r'(?<=git -C )\S+', cmd) or re.search(r'(?:^|[;&|]\s*)cd\s+(?:/d\s+)?([^\s;&|]+)', cmd)
    if not m:
        return cwd
    return (m.group(1) if m.lastindex else m.group(0)).strip('\'"')


def message_of(cmd):
    """Best-effort commit message: heredoc, PowerShell here-string, then -m. None when not found."""
    for pattern in (r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\s*\1\b", r"@'\n(.*?)\n'@", r'@"\n(.*?)\n"@'):
        m = re.search(pattern, cmd, re.S)
        if m:
            return m.group(m.lastindex)
    m = re.search(r'''(?:^|\s)-m\s*(?:"((?:[^"\\]|\\.)*)"|'([^']*)')''', cmd, re.S)
    return (m.group(1) or m.group(2)) if m else None


def tokens(text):
    return re.findall(r'''"[^"]*"|'[^']*'|\S+''', text)


def check_commit(cmd, head, cwd):
    repo = repo_dir(cmd, cwd)
    reasons = []
    if EM_DASH in cmd:
        reasons.append('Em dash in the commit message (banned by the writing rules).')
    if ATTRIBUTION.search(cmd):
        reasons.append('AI or tool attribution in the commit message (no Co-Authored-By, no "generated with").')
    unquoted = re.sub(r'"[^"]*"|\'[^\']*\'', '', head)
    if re.search(r'--no-verify|--no-gpg-sign|commit\.gpgsign=false|(?:^|\s)-[a-zA-Z]*n[a-zA-Z]*(?:\s|$)', unquoted.split('commit', 1)[-1]):
        reasons.append('--no-verify / --no-gpg-sign: hooks and signing are not bypassed without an explicit request.')
    who = git(repo, 'config', 'user.name') + '\n' + git(repo, 'config', 'user.email')
    if re.search(r'^claude( code)?$|anthropic', who, re.I | re.M) or re.search(r'--author[= ]\S*(claude|anthropic)', cmd, re.I):
        reasons.append('Git identity or --author names Claude/Anthropic. Commits carry the user\'s identity.')
    staged = git(repo, 'diff', '--cached', '--name-only').splitlines()
    bad = [p for p in staged if GAME_FILES.search(p)]
    if bad:
        reasons.append('Staged game data (the port ships no game files): ' + ', '.join(bad[:5]))
    subject = (message_of(cmd) or '').strip().split('\n')[0]
    if subject and not SUBJECT.match(subject):
        reasons.append(f'Commit subject "{subject[:70]}" does not match "Type(Scope): past-tense summary (#issue)". '
                       'Types: Feat Fix Docs Chore Refactor Test Perf Build CI Style Revert. Example: '
                       'Fix(Game): avoided BMI1 in the timed QTE stub (#818)')
    if reasons:
        block(*reasons)


def check_push(head, cwd, cmd):
    m = re.search(GIT + r'push\b([^&;|\n]*)', head)
    if not m:
        return
    repo = repo_dir(cmd, cwd)
    args = tokens(m.group(1))
    options = [a for a in args if a.startswith('-') or a.startswith('+')]
    positional = [a.strip('\'"') for a in args if not a.startswith('-')]
    refs = [r for r in positional[1:] if r != 'HEAD']  # first positional is the remote; bare HEAD is the current branch
    reasons = []
    for ref in positional:
        if re.fullmatch(r'\+?(?:[^:]*:)?(?:refs/heads/)?(main|master)', ref):
            reasons.append('Push naming main/master. Open a PR from a branch instead.')
            break
    branch = git(repo, 'branch', '--show-current')
    if branch in ('main', 'master') and not refs and '--tags' not in options:
        reasons.append(f'No explicit branch while on {branch}: this pushes {branch}. Switch to a branch first.')
    if '--all' in options or '--mirror' in options:
        reasons.append('git push --all/--mirror also pushes main. Push the one branch you mean.')
    force = any(o in ('--force', '-f') or (o.startswith('+') and len(o) > 1) for o in options + positional)
    if force or any(r.startswith('+') for r in positional):
        reasons.append('Force push. Use --force-with-lease, and never on a shared branch.')
    if reasons:
        block(*reasons)


def check_gh(cmd, head):
    m = re.search(LEAD + r'gh\s+(issue|pr)\s+(\w+)', head)
    if not m:
        return
    kind, action = m.groups()
    reasons = []
    if not re.search(r'(?:\s-R[\s=]|\s--repo[\s=])', head):
        reasons.append(f'gh {kind} {action} without -R. This clone has no gh default repo: pass -R {UPSTREAM}.')
    text = cmd
    for flag in re.finditer(r'(?:--body-file|-F)[ =]+(\S+)', head):
        path = flag.group(1).strip('\'"')
        if path != '-' and os.path.isfile(path):
            with open(path, encoding='utf-8', errors='replace') as handle:
                text += '\n' + handle.read()
    if action in ('create', 'edit', 'comment', 'review', 'close', 'reopen'):
        if EM_DASH in text:
            reasons.append('Em dash in the issue/PR text (banned by the writing rules).')
        if ATTRIBUTION.search(text):
            reasons.append('AI or tool attribution in the issue/PR text.')
    comments = action in ('comment', 'review') or (action == 'close' and re.search(r'\s(?:--comment|-c)[\s=]', head))
    has_body = re.search(r'--body\b|-b\s|--body-file|-F\s|--comment|-c\s', head)
    if comments and has_body and not ('**EN:**' in text and '**PT-BR:**' in text):
        reasons.append('Comment is not bilingual.\n' + BILINGUAL_HELP)
    if reasons:
        block(*reasons)


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode('utf-8', 'replace') or '{}')
    except ValueError:
        return
    cmd = (data.get('tool_input') or {}).get('command') or ''
    cwd = data.get('cwd') or os.environ.get('CLAUDE_PROJECT_DIR') or '.'
    head = head_of(cmd)
    if re.search(GIT + r'commit\b', head):
        check_commit(cmd, head, cwd)
    if re.search(GIT + r'push\b', head):
        check_push(head, cwd, cmd)
    if re.search(LEAD + r'gh\s+(?:issue|pr)\b', head):
        check_gh(cmd, head)


if __name__ == '__main__':
    main()
