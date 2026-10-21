"""Verify bundled source integrity against the generated archive manifest."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    manifest=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    bad=[]
    for path,expected in manifest['files'].items():
        fp=ROOT/path
        if not fp.is_file():
            bad.append((path,'missing'))
        elif hashlib.sha256(fp.read_bytes()).hexdigest()!=expected:
            bad.append((path,'modified'))
    print(f"Checked {len(manifest['files'])} source files")
    if bad:
        for path,kind in bad:print('[WARN]',kind,path)
        print('An edited file may be intentional; compare it with the original ZIP.')
        return 1
    print('[OK] Source files match the package manifest')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
