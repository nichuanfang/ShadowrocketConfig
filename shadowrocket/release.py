"""Prepare the release plan consumed by the GitHub Actions publisher."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadowrocket.manifest import load_profiles
from shadowrocket.rendering import read_file, validate_profile, without_generated_header
from shadowrocket.storage import write_json_atomic


RELEASE_PLAN_RELATIVE_PATH = Path("dist/release-plan.json")


def build_release_plan(project_root: Path) -> dict[str, Any]:
    """Validate every release artifact and describe the ordered Gist updates."""
    project_root = Path(project_root).resolve()
    items = []

    for definition in load_profiles(project_root):
        if definition.gist_secret is None:
            continue

        relative_path = definition.artifact_relative_path()
        absolute_path = project_root / relative_path
        if not absolute_path.is_file():
            raise FileNotFoundError(
                "Release artifact for {!r} does not exist: {}".format(definition.id, absolute_path)
            )

        content = read_file(absolute_path)
        if not content.strip():
            raise ValueError("Release artifact for {!r} is empty: {}".format(definition.id, relative_path))
        if definition.is_regular_profile:
            validate_profile(
                without_generated_header(content),
                relative_path.as_posix(),
                check_placeholders=False,
            )

        items.append(
            {
                "id": definition.id,
                "path": relative_path.as_posix(),
                "gist_file": (definition.source.name if definition.source is not None else relative_path.name),
                "gist_secret": definition.gist_secret,
            }
        )

    return {"version": 1, "items": items}


def write_release_plan(project_root: Path, plan: dict[str, Any]) -> Path:
    """Persist the release plan inside dist/ for the workflow publisher."""
    destination = Path(project_root).resolve() / RELEASE_PLAN_RELATIVE_PATH
    write_json_atomic(destination, plan)
    return destination
