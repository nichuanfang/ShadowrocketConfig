"""Load the profile manifest that drives generation and publishing."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


MANIFEST_RELATIVE_PATH = Path("config/profiles.toml")
PROFILE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
SECRET_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
PROFILE_FIELDS = frozenset({"id", "template", "source", "gist_secret"})
SOURCE_PATTERNS = (
    (re.compile(r"^shadowrocket_[a-z0-9_-]+\.conf$"), None),
    (re.compile(r"^[A-Za-z0-9_-]+\.sg?module$"), PurePosixPath("module")),
)


class ManifestError(ValueError):
    """Raised when the profile manifest is incomplete or inconsistent."""


@dataclass(frozen=True)
class ProfileDefinition:
    """One generated or static profile and its optional release target."""

    id: str
    template: PurePosixPath | None
    source: PurePosixPath | None
    gist_secret: str | None

    @property
    def output_relative_path(self) -> Path:
        return Path("dist") / "shadowrocket_{}.conf".format(self.id)

    @property
    def strategy_filename(self) -> str:
        return "shadowrocket_{}.conf".format(self.id)

    @property
    def is_regular_profile(self) -> bool:
        """Whether the artifact contains the standard Shadowrocket .conf sections."""
        relative_path = self.artifact_relative_path()
        return relative_path.suffix == ".conf"

    def artifact_relative_path(self) -> Path:
        """Return the file that should be published for this profile."""
        if self.template is not None:
            return self.output_relative_path
        assert self.source is not None
        return Path(self.source.as_posix())


def load_profiles(project_root: Path) -> list[ProfileDefinition]:
    """Load and validate the manifest against a project checkout."""
    project_root = Path(project_root).resolve()
    manifest_path = project_root / MANIFEST_RELATIVE_PATH
    try:
        data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError("Profile manifest not found: {}".format(manifest_path)) from None

    unknown_root_fields = set(data).difference({"profiles"})
    if unknown_root_fields:
        raise ManifestError(
            "Unknown field(s) in {}: {}".format(
                manifest_path, _format_names(unknown_root_fields)
            )
        )

    raw_profiles = data.get("profiles")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise ManifestError("{} must define a non-empty [[profiles]] list".format(manifest_path))

    profiles = []
    seen_ids = set()
    seen_secrets = set()
    for index, raw_profile in enumerate(raw_profiles, start=1):
        if not isinstance(raw_profile, dict):
            raise ManifestError("Profile entry {} must be a table".format(index))

        unknown_fields = set(raw_profile).difference(PROFILE_FIELDS)
        if unknown_fields:
            raise ManifestError(
                "Unknown field(s) in profile entry {} of {}: {}".format(
                    index, manifest_path, _format_names(unknown_fields)
                )
            )

        profile_id = raw_profile.get("id")
        if not isinstance(profile_id, str) or not PROFILE_ID_PATTERN.fullmatch(profile_id):
            raise ManifestError(
                "Profile entry {} has an invalid id; use lowercase letters, digits, '_' or '-'".format(index)
            )
        if profile_id in seen_ids:
            raise ManifestError("Duplicate profile id in {}: {}".format(manifest_path, profile_id))
        seen_ids.add(profile_id)

        template = _optional_relative_path(raw_profile, "template", project_root, manifest_path)
        source = _optional_relative_path(raw_profile, "source", project_root, manifest_path)
        if (template is None) == (source is None):
            raise ManifestError(
                "Profile {!r} must define exactly one of 'template' or 'source'".format(profile_id)
            )

        if template is not None and template.parent != PurePosixPath("config/strategy"):
            raise ManifestError(
                "Profile {!r} template must be directly under config/strategy: {}".format(profile_id, template)
            )

        gist_secret = raw_profile.get("gist_secret")
        if gist_secret is not None:
            if not isinstance(gist_secret, str) or not SECRET_NAME_PATTERN.fullmatch(gist_secret):
                raise ManifestError(
                    "Profile {!r} has an invalid gist_secret; use an uppercase environment name".format(profile_id)
                )
            if gist_secret in seen_secrets:
                raise ManifestError(
                    "Duplicate gist_secret in {}: {}".format(manifest_path, gist_secret)
                )
            seen_secrets.add(gist_secret)

        profiles.append(
            ProfileDefinition(
                id=profile_id,
                template=template,
                source=source,
                gist_secret=gist_secret,
            )
        )

    return profiles


def _optional_relative_path(
    profile: dict[str, Any],
    field: str,
    project_root: Path,
    manifest_path: Path,
) -> PurePosixPath | None:
    value = profile.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ManifestError("Profile field {!r} must be a non-empty path".format(field))

    relative_path = PurePosixPath(value)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ManifestError("Profile field {!r} must stay inside the project: {}".format(field, value))
    if field == "template" and relative_path.suffix != ".conf":
        raise ManifestError("Profile field 'template' must point to a .conf file: {}".format(value))
    if field == "source" and not _is_valid_source(relative_path):
        raise ManifestError(
            "Profile field 'source' must be a shadowrocket_*.conf or module/*.module file: {}".format(value)
        )

    absolute_path = (project_root / relative_path).resolve()
    try:
        absolute_path.relative_to(project_root)
    except ValueError:
        raise ManifestError(
            "Profile field {!r} escapes the project: {}".format(field, value)
        ) from None
    if not absolute_path.is_file():
        raise FileNotFoundError(
            "Profile file referenced by {} does not exist: {}".format(manifest_path, absolute_path)
        )
    return relative_path


def _is_valid_source(relative_path: PurePosixPath) -> bool:
    for name_pattern, parent in SOURCE_PATTERNS:
        if name_pattern.fullmatch(relative_path.name) and (
            parent is None or relative_path.parent == parent
        ):
            return True
    return False


def _format_names(names: set[str]) -> str:
    return ", ".join(sorted(names))
