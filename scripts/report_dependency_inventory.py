"""Inventory Ripple's checked-in dependency surfaces without network access."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

_REQ_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)(?P<extras>\[[^\]]+\])?(?P<spec>==|>=|<=|~=|>|<)(?P<version>[A-Za-z0-9][^\s;=<>!~]*)$"
)
_DOCKER_RE = re.compile(r"^FROM\s+(?P<image>[^\s]+)(?:\s+AS\s+(?P<stage>\S+))?$", re.MULTILINE)
_ACTION_RE = re.compile(r"^\s*uses:\s*(?P<action>[^@\s]+)@(?P<version>\S+)\s*$", re.MULTILINE)
_COMPOSE_IMAGE_RE = re.compile(r"^\s*image:\s*(?P<image>[^\s#]+)", re.MULTILINE)
_PROVIDER_RE = re.compile(
    r"(?P<name>[A-Za-z0-9_-]+)\s*=\s*\{[^}]*?source\s*=\s*\"(?P<source>[^\"]+)\"[^}]*?version\s*=\s*\"(?P<version>[^\"]+)\"",
    re.DOTALL,
)


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _source(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def _requirements(path: Path, classification: str, root: Path) -> list[dict]:
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-r "):
            continue
        match = _REQ_RE.fullmatch(line)
        if match is None:
            rows.append(
                {
                    "surface": "python",
                    "classification": classification,
                    "name": line,
                    "version": None,
                    "source": _source(path, root),
                    "parse_status": "unrecognized",
                }
            )
            continue
        rows.append(
            {
                "surface": "python",
                "classification": classification,
                "name": _normalize(match.group("name")),
                "version": match.group("spec") + match.group("version"),
                "source": _source(path, root),
                "parse_status": "ok",
            }
        )
    return rows


def _docker_images(path: Path, root: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    rows = []
    for match in _DOCKER_RE.finditer(text):
        image = match.group("image")
        rows.append(
            {
                "surface": "docker",
                "classification": "runtime_image",
                "name": image.split(":")[0],
                "version": image.split(":", 1)[1] if ":" in image else None,
                "source": _source(path, root),
                "stage": match.group("stage"),
                "parse_status": "ok",
            }
        )
    return rows


def _compose_images(path: Path, root: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    rows = []
    for match in _COMPOSE_IMAGE_RE.finditer(text):
        image = match.group("image")
        rows.append(
            {
                "surface": "docker",
                "classification": "compose_image",
                "name": image.split(":")[0],
                "version": image.split(":", 1)[1] if ":" in image else None,
                "source": _source(path, root),
                "stage": None,
                "parse_status": "ok",
            }
        )
    return rows


def _actions(path: Path, root: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    return [
        {
            "surface": "github_actions",
            "classification": "ci_action",
            "name": match.group("action"),
            "version": match.group("version"),
            "source": _source(path, root),
            "parse_status": "ok",
        }
        for match in _ACTION_RE.finditer(text)
    ]


def _terraform(path: Path, root: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    rows = []
    for match in _PROVIDER_RE.finditer(text):
        rows.append(
            {
                "surface": "terraform",
                "classification": "provider",
                "name": match.group("source"),
                "version": match.group("version"),
                "source": _source(path, root),
                "parse_status": "ok",
            }
        )
    required = re.search(r'required_version\s*=\s*"([^"]+)"', text)
    if required:
        rows.append(
            {
                "surface": "terraform",
                "classification": "terraform_cli",
                "name": "terraform",
                "version": required.group(1),
                "source": _source(path, root),
                "parse_status": "ok",
            }
        )
    return rows


def build_inventory(root: Path = ROOT) -> dict:
    direct = _requirements(root / "requirements.in", "direct", root)
    locked = _requirements(root / "requirements.txt", "locked", root)
    dev = _requirements(root / "requirements-dev.txt", "development", root)
    docker = _docker_images(root / "Dockerfile", root)
    docker += _compose_images(root / "compose.production.yaml", root)
    actions = _actions(root / ".github" / "workflows" / "ci.yml", root)
    terraform = _terraform(root / "infra" / "terraform" / "versions.tf", root)

    entries = direct + locked + dev + docker + actions + terraform
    return {
        "format": "ripple-dependency-inventory",
        "version": 1,
        "network_accessed": False,
        "entries": entries,
        "counts": {
            "total": len(entries),
            "python": sum(item["surface"] == "python" for item in entries),
            "docker": sum(item["surface"] == "docker" for item in entries),
            "github_actions": sum(item["surface"] == "github_actions" for item in entries),
            "terraform": sum(item["surface"] == "terraform" for item in entries),
        },
        "unrecognized": [
            item for item in entries if item.get("parse_status") != "ok"
        ],
    }


def render_text(inventory: dict) -> str:
    lines = [
        "Ripple dependency inventory",
        f"Total entries: {inventory['counts']['total']}",
        "",
    ]
    for surface in ("python", "docker", "github_actions", "terraform"):
        lines.append(f"{surface}:")
        for item in inventory["entries"]:
            if item["surface"] != surface:
                continue
            lines.append(
                f"- {item['classification']}: {item['name']} {item['version'] or '(unversioned)'} "
                f"[{item['source']}]"
            )
        lines.append("")
    lines.append("This inventory is local-only and does not determine whether a dependency is current.")
    return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    inventory = build_inventory()
    print(json.dumps(inventory, indent=2, sort_keys=True) if args.json else render_text(inventory))
    return 1 if inventory["unrecognized"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
