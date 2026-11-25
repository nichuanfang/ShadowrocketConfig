"""Build Shadowrocket profiles and optionally prepare their Gist release."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence

if sys.version_info < (3, 11):
    raise RuntimeError("ShadowrocketConfig requires Python 3.11 or newer")

from shadowrocket.manifest import ProfileDefinition, load_profiles
from shadowrocket.release import build_release_plan, write_release_plan
from shadowrocket.rendering import (
    PLACEHOLDER_PATTERN,
    REQUIRED_SECTIONS,
    render_profiles as _render_profiles,
)
from shadowrocket.storage import write_profiles as _write_profiles


PROJECT_ROOT = Path(__file__).resolve().parent
STRATEGY_FILES = tuple(
    definition.strategy_filename
    for definition in load_profiles(PROJECT_ROOT)
    if definition.template is not None
)


def render_profiles(
    project_root: Path = PROJECT_ROOT,
    generated_at: datetime | None = None,
) -> dict[str, str]:
    """Render and validate every generated profile without writing files."""
    return _render_profiles(project_root, generated_at)


def load_profile_definitions(project_root: Path = PROJECT_ROOT) -> list[ProfileDefinition]:
    """Expose the manifest definitions for generation and release tooling."""
    return load_profiles(project_root)


def write_profiles(project_root: Path, profiles: Mapping[str, str]) -> None:
    """Stage all generated files, then atomically replace their destinations."""
    _write_profiles(project_root, profiles)


def main(argv: Sequence[str] | None = None) -> None:
    """Build all supported profiles and optionally prepare the release plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release",
        action="store_true",
        help="validate release artifacts and write dist/release-plan.json",
    )
    args = parser.parse_args(argv)

    profiles = render_profiles(PROJECT_ROOT)
    write_profiles(PROJECT_ROOT, profiles)
    if not args.release:
        return

    expected_outputs = {
        definition.output_relative_path.name
        for definition in load_profiles(PROJECT_ROOT)
        if definition.template is not None
    }
    unexpected_outputs = set(profiles).difference(expected_outputs)
    if unexpected_outputs:
        raise ValueError(
            "Unexpected generated profile(s): {}".format(", ".join(sorted(unexpected_outputs)))
        )
    write_release_plan(PROJECT_ROOT, build_release_plan(PROJECT_ROOT))


if __name__ == "__main__":
    main()
