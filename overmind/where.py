from __future__ import annotations

import json
from pathlib import Path

import overmind


def resolve_locations() -> dict[str, str]:
    package_init = Path(overmind.__file__).resolve()
    package_dir = package_init.parent
    project_root = package_dir.parent
    return {
        "project_root": str(project_root),
        "package_dir": str(package_dir),
        "package_init": str(package_init),
        "demo_module": str((package_dir / "demo.py").resolve()),
        "main_module": str((package_dir / "main.py").resolve()),
    }


def main() -> None:
    print(json.dumps(resolve_locations(), indent=2))


if __name__ == "__main__":
    main()
