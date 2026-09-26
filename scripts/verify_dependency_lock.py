"""Validate that direct runtime dependency intent is represented by the lock file."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIRECT = ROOT / "requirements.in"
LOCK = ROOT / "requirements.txt"

_REQ_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)(?P<extras>\[[^\]]+\])?(?P<spec>==|>=)(?P<version>[A-Za-z0-9][^\s;=<>!~]*)$"
)


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse(path: Path) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-r "):
            continue
        match = _REQ_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"unsupported requirement syntax in {path.name}: {line}")
        key = _normalize(match.group("name"))
        entries[key] = (match.group("spec"), match.group("version"))
    return entries


def verify_dependency_lock() -> list[str]:
    errors: list[str] = []
    if not DIRECT.is_file():
        return ["requirements.in is missing."]
    if not LOCK.is_file():
        return ["requirements.txt is missing."]

    try:
        direct = _parse(DIRECT)
        locked = _parse(LOCK)
    except ValueError as exc:
        return [str(exc)]

    for name, direct_requirement in sorted(direct.items()):
        locked_requirement = locked.get(name)
        if locked_requirement is None:
            errors.append(f"{name}: missing from requirements.txt")
            continue
        if locked_requirement != direct_requirement:
            errors.append(
                f"{name}: requirements.in {direct_requirement[0]}{direct_requirement[1]} "
                f"does not match requirements.txt {locked_requirement[0]}{locked_requirement[1]}"
            )

    return errors


def main() -> int:
    errors = verify_dependency_lock()
    if errors:
        print("Dependency lock verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Dependency lock verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
