from pathlib import Path
from zipfile import ZipFile

from overmind.export import build_project_zip


def test_build_project_zip_creates_archive(tmp_path: Path) -> None:
    archive = build_project_zip(output=str(tmp_path / "bundle.zip"))
    assert archive.exists()

    with ZipFile(archive, "r") as zf:
        names = set(zf.namelist())
        assert "README.md" in names
        assert "pyproject.toml" in names
        assert any(name.startswith("overmind/") for name in names)
