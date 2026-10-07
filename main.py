"""Build the Shadowrocket configuration profiles in ``dist/``."""

import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Mapping, Optional


PROJECT_ROOT = Path(__file__).resolve().parent
STRATEGY_FILES = (
    "black.conf",
    "black_ad.conf",
    "black_accelerate.conf",
    "black_accelerate_ad.conf",
    "white.conf",
    "white_ad.conf",
    "white_accelerate.conf",
    "white_accelerate_ad.conf",
)
PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")
SECTION_PATTERN = re.compile(r"^\s*\[([^\]]+)\]\s*$")
REQUIRED_SECTIONS = ("General", "Rule", "Host", "URL Rewrite")


def read_file(file_path: Path) -> str:
    """Read a UTF-8 project input file."""
    return file_path.read_text(encoding="utf-8")


def _read_fragments(project_root: Path) -> Dict[str, str]:
    """Load common inputs once for one deterministic render pass."""
    inputs = {
        "general": project_root / "config/general/general.conf",
        "base": project_root / "base.conf",
        "custom-direct": project_root / "config/rules/custom_direct.conf",
        "custom-proxy": project_root / "config/rules/custom_proxy.conf",
        "custom-reject": project_root / "config/rules/custom_reject.conf",
        "direct": project_root / "config/rules/direct.conf",
        "reject": project_root / "config/rules/reject.conf",
        "proxy": project_root / "config/rules/proxy.conf",
        "direct-accelerate": project_root / "config/rules/direct_accelerate.conf",
        "proxy-accelerate": project_root / "config/rules/proxy_accelerate.conf",
    }
    return {name: read_file(path) for name, path in inputs.items()}


def _resolve_template(template: str, replacements: Mapping[str, str], source: Path) -> str:
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


def _validate_profile(content: str, source: str) -> None:
    """Reject malformed generated profiles before any output is written."""
    if PLACEHOLDER_PATTERN.search(content):
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
    project_root: Path = PROJECT_ROOT,
    generated_at: Optional[datetime] = None,
) -> Dict[str, str]:
    """Render and validate every profile without writing files or using the network."""
    project_root = Path(project_root).resolve()
    fragments = _read_fragments(project_root)
    timestamp = generated_at or datetime.now()
    header = timestamp.strftime("# Shadowrocket: %Y-%m-%d %H:%M:%S")

    replacements = {name: value for name, value in fragments.items() if name not in ("general", "base")}
    profiles = {}

    for strategy_name in STRATEGY_FILES:
        strategy_path = project_root / "config/strategy" / strategy_name
        strategy = _resolve_template(read_file(strategy_path), replacements, strategy_path)
        content = "\n".join(
            (
                header,
                "[General]",
                fragments["general"].rstrip("\n"),
                "",
                "[Rule]",
                "",
                strategy.rstrip("\n"),
                "",
                fragments["base"].rstrip("\n"),
                "",
            )
        )
        _validate_profile(content, strategy_name)
        profiles["shadowrocket_" + strategy_name] = content

    return profiles


def write_profiles(project_root: Path, profiles: Mapping[str, str]) -> None:
    """Stage all generated files, then atomically replace their destinations."""
    project_root = Path(project_root).resolve()
    for filename, content in profiles.items():
        if Path(filename).name != filename:
            raise ValueError("Invalid profile output filename: {}".format(filename))
        _validate_profile(content, filename)

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


def main() -> None:
    """Build all supported profiles using paths relative to this script."""
    profiles = render_profiles(PROJECT_ROOT)
    write_profiles(PROJECT_ROOT, profiles)


if __name__ == "__main__":
    main()
