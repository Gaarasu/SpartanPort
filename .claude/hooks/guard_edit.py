#!/usr/bin/env python3
"""PreToolUse hook for Edit and Write.

- Blocks edits to tracked files while on main/master (work happens on a branch).
  Gitignored files, .claude/ and CLAUDE.md are exempt so agent config can be maintained anywhere.
- Asks before editing inside a git submodule: those trees are shared and not part of this repo's
  history. Changes to FSR-Vulkan belong in gpu/patches/<name>/*.patch, which build.sh applies.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def git(repo, *args):
    try:
        done = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    return done if done.returncode == 0 else None


def submodule_paths(root):
    config = root / '.gitmodules'
    if not config.is_file():
        return []
    paths = []
    for line in config.read_text(encoding='utf-8', errors='replace').splitlines():
        key, _, value = line.strip().partition('=')
        if key.strip() == 'path':
            paths.append(value.strip())
    return paths


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode('utf-8', 'replace') or '{}')
    except ValueError:
        return
    target = (data.get('tool_input') or {}).get('file_path')
    if not target:
        return
    target = Path(target)
    probe = target.parent
    while not probe.is_dir() and probe != probe.parent:
        probe = probe.parent
    top = git(probe, 'rev-parse', '--show-toplevel')
    if not top:
        return
    root = Path(top.stdout.strip()).resolve()
    project = Path(os.environ.get('CLAUDE_PROJECT_DIR') or data.get('cwd') or root).resolve()
    if root != project:
        return  # a different repo (or a submodule's own root): not governed by this project's rules
    try:
        rel = target.resolve().relative_to(root).as_posix()
    except ValueError:
        return

    for sub in submodule_paths(root):
        if rel == sub or rel.startswith(sub + '/'):
            json.dump({'hookSpecificOutput': {
                'hookEventName': 'PreToolUse', 'permissionDecision': 'ask',
                'permissionDecisionReason': f'{sub} is a git submodule. This repo changes it only through '
                                            f'gpu/patches/<name>/*.patch (applied by build.sh). Edit it directly anyway?'}},
                      sys.stdout)
            return

    if rel.startswith('.claude/') or rel == 'CLAUDE.md':
        return
    branch = git(root, 'branch', '--show-current')
    if branch and branch.stdout.strip() in ('main', 'master'):
        ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '-q', '--', rel]).returncode == 0
        if not ignored:
            sys.stderr.write('Blocked by project CLAUDE.md rules:\n'
                             '- You are on main. Create a short-lived branch (feat/, fix/, chore/, docs/) '
                             'before editing tracked files.\n')
            sys.exit(2)


if __name__ == '__main__':
    main()
