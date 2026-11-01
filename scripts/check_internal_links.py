"""Fail when a relative Markdown file link points to a missing path."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')


def main() -> int:
    failures = []
    for document in ROOT.rglob('*.md'):
        if any(part.startswith('.') for part in document.relative_to(ROOT).parts):
            continue
        for target in LINK.findall(document.read_text(errors='replace')):
            value = target.strip().split()[0].strip('<>')
            if not value or value.startswith(('#', 'http://', 'https://', 'mailto:')):
                continue
            path_text = unquote(value.split('#', 1)[0])
            if path_text and not (document.parent / path_text).resolve().exists():
                failures.append('%s -> %s' % (document.relative_to(ROOT), value))
    if failures:
        print('\n'.join(failures))
        return 1
    print('Internal Markdown links: ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
