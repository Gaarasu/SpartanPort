#!/usr/bin/env python3
"""SessionStart hook: one line of build-environment facts, so nobody assumes a toolchain that is not there.

stdout of a SessionStart hook is added to the session context.
"""
import os
import shutil
import subprocess
from pathlib import Path


def run(*args):
    try:
        done = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20)
    except (OSError, subprocess.SubprocessError):
        return ''
    return done.stdout.strip() if done.returncode == 0 else ''


def main():
    root = Path(os.environ.get('CLAUDE_PROJECT_DIR') or '.')
    branch = run('git', '-C', str(root), 'branch', '--show-current') or '(detached)'
    modules = run('git', '-C', str(root), 'submodule', 'status').splitlines()
    missing = sum(1 for line in modules if line.startswith('-'))
    facts = [f'branch {branch}']
    facts.append(f'submodules {len(modules) - missing}/{len(modules)} initialized'
                 + (' (git submodule update --init --recursive before build.sh)' if missing else ''))
    if os.name == 'nt':
        msys = Path(os.environ.get('MSYS2_ROOT', 'C:/msys64')) / 'clang64' / 'bin'
        facts.append('MSYS2 CLANG64 ' + ('found' if msys.is_dir() else 'NOT found (C/C++ cannot be built)'))
    else:
        facts.append('gcc ' + ('found' if shutil.which('gcc') else 'NOT found'))
    try:
        import iced_x86  # noqa: F401
        facts.append('iced-x86 present')
    except ImportError:
        facts.append('iced-x86 missing (test_hook_isa and test_isa_rewrite are skipped)')
    facts.append('out/ ' + ('has a build' if (root / 'out').is_dir() else 'empty'))
    print('SpartanPort environment: ' + ' | '.join(facts))


if __name__ == '__main__':
    main()
