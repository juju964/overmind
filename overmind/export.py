from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def build_project_zip(output: str = "overmind-project.zip") -> Path:
    root = Path(__file__).resolve().parents[1]
    out_path = (root / output).resolve()

    include_dirs = {"overmind", "tests"}
    include_files = {"README.md", "pyproject.toml", ".gitignore"}

    with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as zf:
        for file_name in include_files:
            candidate = root / file_name
            if candidate.exists():
                zf.write(candidate, arcname=file_name)

        for d in include_dirs:
            folder = root / d
            if not folder.exists():
                continue
            for path in folder.rglob("*"):
                if path.is_file():
                    zf.write(path, arcname=str(path.relative_to(root)))

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a zip archive of the Overmind project")
    parser.add_argument("--output", default="overmind-project.zip", help="Output zip file name")
    args = parser.parse_args()

    archive = build_project_zip(args.output)
    print(f"Archive created: {archive}")


if __name__ == "__main__":
    main()
