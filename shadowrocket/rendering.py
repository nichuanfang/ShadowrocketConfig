"""Render Shadowrocket profiles from the manifest and rule fragments."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Mapping

from shadowrocket.manifest import load_profiles


PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")
SECTION_PATTERN = re.compile(r"^\s*\[([^\]]+)\]\s*$")
REQUIRED_SECTIONS = ("General", "Rule", "Host", "URL Rewrite")
GENERAL_PATH = Path("config/general/general.conf")
BASE_PATH = Path("base.conf")
RULES_DIRECTORY = Path("config/rules")
GENERATED_HEADER_PATTERN = re.compile(r"^# Shadowrocket: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\n")


def read_file(file_path: Path) -> str:
    """Read a UTF-8 project input file."""
    return file_path.read_text(encoding="utf-8")


def load_rule_fragments(project_root: Path) -> dict[str, str]:
    """Load every rule fragment using its filename as the placeholder name."""
    project_root = Path(project_root).resolve()
    fragments = {}
    for path in sorted((project_root / RULES_DIRECTORY).glob("*.conf")):
        name = path.stem.replace("_", "-")
        if name in fragments:
            raise ValueError(
                "Duplicate rule fragment name {!r}; filenames must map to unique placeholders".format(name)
            )
        fragments[name] = read_file(path)
    if not fragments:
        raise FileNotFoundError("No rule fragments found in {}".format(project_root / RULES_DIRECTORY))
    return fragments


def resolve_template(template: str, replacements: Mapping[str, str], source: Path) -> str:
    placeholders = set(PLACEHOLDER_PATTERN.findall(template))
    unknown = placeholders.difference(replacements)
    if unknown:
        names = ", ".join("{" + name + "}" for name in sorted(unknown))
        raise ValueError("Unknown placeholder(s) in {}: {}".format(source, names))

    rendered = PLACEHOLDER_PATTERN.sub(
        lambda match: replacements[match.group(1)], template
    )
    unresolved = PLACEHOLDER_PATTERN.findall(rendered)
    if unresolved:
        names = ", ".join("{" + name + "}" for name in sorted(set(unresolved)))
        raise ValueError("Unresolved placeholder(s) in {}: {}".format(source, names))
    return rendered


def validate_profile(content: str, source: str, *, check_placeholders: bool = True) -> None:
    """Reject malformed generated or published profiles before writing."""
    if check_placeholders and PLACEHOLDER_PATTERN.search(content):
        raise ValueError("Unresolved placeholder in generated profile {}".format(source))
    sections = []
    current_section = None
    rule_lines = []
    for line in content.splitlines():
        section_match = SECTION_PATTERN.match(line)
        if section_match:
            current_section = section_match.group(1).strip()
            sections.append(current_section)
            continue
        if current_section == "Rule":
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                rule_lines.append(stripped)

    for section in REQUIRED_SECTIONS:
        count = sections.count(section)
        if count != 1:
            raise ValueError(
                "{} must contain exactly one [{}] section; found {}".format(
                    source, section, count
                )
            )

    final_rules = [line for line in rule_lines if line.upper().startswith("FINAL,")]
    if (
        len(final_rules) != 1
        or not rule_lines
        or not rule_lines[-1].upper().startswith("FINAL,")
    ):
        raise ValueError(
            "{} must end its [Rule] section with exactly one FINAL rule".format(source)
        )


def render_profiles(
    project_root: Path,
    generated_at: datetime | None = None,
) -> dict[str, str]:
    """Render and validate every generated profile without writing files."""
    project_root = Path(project_root).resolve()
    definitions = load_profiles(project_root)
    fragments = load_rule_fragments(project_root)
    general = read_file(project_root / GENERAL_PATH)
    base = read_file(project_root / BASE_PATH)
    timestamp = generated_at or datetime.now()
    header = timestamp.strftime("# Shadowrocket: %Y-%m-%d %H:%M:%S")

    profiles = {}
    for definition in definitions:
        if definition.template is None:
            continue

        template_path = project_root / definition.template
        strategy = resolve_template(read_file(template_path), fragments, template_path)
        content = "\n".join(
            (
                header,
                "[General]",
                general.rstrip("\n"),
                "",
                "[Rule]",
                "",
                strategy.rstrip("\n"),
                "",
                base.rstrip("\n"),
                "",
            )
        )
        validate_profile(content, definition.strategy_filename)
        profiles[definition.strategy_filename] = content

    return profiles


def without_generated_header(content: str) -> str:
    """Remove only the timestamped header used to identify generated profiles."""
    return GENERATED_HEADER_PATTERN.sub("", content, count=1)
