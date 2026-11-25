"""Atomically write rendered profiles and release metadata."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from shadowrocket.rendering import validate_profile


def write_profiles(project_root: Path, profiles: Mapping[str, str]) -> None:
    """Stage all generated files, then atomically replace their destinations."""
    project_root = Path(project_root).resolve()
    for filename, content in profiles.items():
        if Path(filename).name != filename:
            raise ValueError("Invalid profile output filename: {}".format(filename))
        validate_profile(content, filename)

    output_dir = project_root / "dist"
    output_dir.mkdir(parents=True, exist_ok=True)
    staged = []

    try:
        for filename, content in profiles.items():
            destination = output_dir / filename
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix="." + filename + ".",
                suffix=".tmp",
                dir=str(output_dir),
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                staged.append((temporary_path, destination))
                temporary.write(content)
            os.chmod(str(temporary_path), 0o644)

        for temporary_path, destination in staged:
            os.replace(str(temporary_path), str(destination))
    finally:
        for temporary_path, _ in staged:
            if temporary_path.exists():
                temporary_path.unlink()


def write_json_atomic(destination: Path, value: Any) -> None:
    """Write JSON beside its destination and replace it in one step."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix="." + destination.name + ".",
        suffix=".tmp",
        dir=str(destination.parent),
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
        temporary.write(payload)
    try:
        os.replace(str(temporary_path), str(destination))
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
