"""File receipts and containment rules shared by the bundle operations."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return sha256(stream.read()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)+'\n', encoding='utf-8')


def reject_symlinks(path: Path, *, recursive=False) -> None:
    for item in (path, *path.absolute().parents):
        if item.is_symlink():
            raise ValueError(f'symlink is not allowed: {item}')
    if recursive and path.is_dir():
        for item in path.rglob('*'):
            if item.is_symlink():
                raise ValueError(f'symlink is not allowed: {item}')
            if not item.is_dir() and not item.is_file():
                raise ValueError(f'nonregular file is not allowed: {item}')


def safe_relative(value: str) -> str:
    path=PurePosixPath(value)
    if not value or path.is_absolute() or '..' in path.parts or '\\' in value or str(path)!=value:
        raise ValueError(f'unsafe relative path: {value!r}')
    return value


def inventory(root: Path) -> dict[str,str]:
    reject_symlinks(root, recursive=True)
    return {p.relative_to(root).as_posix():digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and p!=root/'bundle.json'}
