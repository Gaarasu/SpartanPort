#!/usr/bin/env python3
"""PostToolUse hook for Edit and Write: catch a broken file right after it is written.

Python must compile, patch XML must parse, JSON must load. Exit 2 feeds the error back to Claude.
Compiles in memory, so no __pycache__ is left behind.
"""
import json
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode('utf-8', 'replace') or '{}')
    except ValueError:
        return
    target = (data.get('tool_input') or {}).get('file_path')
    if not target or not Path(target).is_file():
        return
    path = Path(target)
    suffix = path.suffix.lower()
    try:
        if suffix == '.py':
            compile(path.read_bytes(), str(path), 'exec')
        elif suffix == '.xml' and 'patches' in path.parts:
            ElementTree.parse(path)
        elif suffix == '.json':
            json.loads(path.read_text(encoding='utf-8'))
    except (SyntaxError, ValueError, ElementTree.ParseError) as error:
        sys.stderr.write(f'{path.name} is not valid after this edit: {error}\n')
        sys.exit(2)


if __name__ == '__main__':
    main()
