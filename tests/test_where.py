from pathlib import Path

from overmind.where import resolve_locations


def test_resolve_locations_points_to_repo_files() -> None:
    data = resolve_locations()
    assert Path(data["project_root"]).exists()
    assert Path(data["package_dir"]).name == "overmind"
    assert Path(data["demo_module"]).name == "demo.py"
    assert Path(data["main_module"]).name == "main.py"
