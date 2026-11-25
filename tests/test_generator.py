import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import main  # noqa: E402


FIXED_TIME = datetime(2026, 1, 2, 3, 4, 5)


class GeneratorTests(unittest.TestCase):
    def test_renders_all_eight_profiles_without_unresolved_placeholders(self):
        profiles = main.render_profiles(PROJECT_ROOT, FIXED_TIME)

        self.assertEqual(len(profiles), 8)
        self.assertEqual(
            set(profiles),
            set(main.STRATEGY_FILES),
        )
        for name, content in profiles.items():
            with self.subTest(profile=name):
                self.assertIn("# Shadowrocket: 2026-01-02 03:04:05", content)
                self.assertTrue(content.endswith("\n"))
                self.assertIsNone(main.PLACEHOLDER_PATTERN.search(content))
                for section in main.REQUIRED_SECTIONS:
                    self.assertEqual(content.count("[{}]".format(section)), 1)

    def test_white_profiles_keep_cn_direct_and_proxy_fallback(self):
        profiles = main.render_profiles(PROJECT_ROOT, FIXED_TIME)
        white_profiles = [name for name in profiles if "_white" in name]

        self.assertTrue(white_profiles)
        for name in white_profiles:
            with self.subTest(profile=name):
                content = profiles[name]
                self.assertIn("GEOIP,cn,DIRECT", content)
                self.assertRegex(content, r"(?m)^FINAL,PROXY$")

    def test_domain_only_china_source_uses_domain_set(self):
        profiles = main.render_profiles(PROJECT_ROOT, FIXED_TIME)
        expected = (
            "DOMAIN-SET,https://raw.githubusercontent.com/blackmatrix7/"
            "ios_rule_script/master/rule/Shadowrocket/ChinaMaxNoIP/"
            "ChinaMaxNoIP_Domain.list,DIRECT"
        )
        self.assertIn(expected, profiles["shadowrocket_white.conf"])
        self.assertNotIn("RULE-SET," + expected.split(",", 1)[1], profiles["shadowrocket_white.conf"])

    def test_balanced_dns_and_udp_settings_are_preserved(self):
        profiles = main.render_profiles(PROJECT_ROOT, FIXED_TIME)
        content = profiles["shadowrocket_white.conf"]

        for setting in (
            "dns-server = https://doh.pub/dns-query,https://dns.alidns.com/dns-query,223.5.5.5,119.29.29.29",
            "fallback-dns-server = system",
            "dns-direct-system = true",
            "dns-direct-fallback-proxy = true",
            "udp-policy-not-supported-behaviour = REJECT",
            "block-quic = all-proxy",
        ):
            with self.subTest(setting=setting):
                self.assertIn(setting, content)

    def test_ad_filter_only_appears_in_ad_profiles(self):
        profiles = main.render_profiles(PROJECT_ROOT, FIXED_TIME)
        marker = "Adblock4limbo.list,REJECT"

        for name, content in profiles.items():
            with self.subTest(profile=name):
                if "_ad" in name:
                    self.assertIn(marker, content)
                else:
                    self.assertNotIn(marker, content)

    def test_published_sources_use_shadowrocket_rules_and_escaped_rewrites(self):
        profiles = main.render_profiles(PROJECT_ROOT, FIXED_TIME)
        published = list(profiles.values()) + [
            (PROJECT_ROOT / "shadowrocket_free.conf").read_text(encoding="utf-8"),
            (PROJECT_ROOT / "README.md").read_text(encoding="utf-8"),
        ]
        for content in published:
            self.assertNotIn("/rule/QuantumultX/", content)

        for source in (
            PROJECT_ROOT / "base.conf",
            PROJECT_ROOT / "shadowrocket_free.conf",
            PROJECT_ROOT / "README.md",
        ):
            with self.subTest(source=source.name):
                text = source.read_text(encoding="utf-8")
                self.assertIn(r"^https?://(www\.)?g\.cn ", text)
                self.assertIn(r"^https?://(www\.)?google\.cn ", text)

    def test_invalid_profile_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            copy_root = temp_root / "project"
            outside = temp_root / "outside"
            outside.mkdir()
            self._copy_build_inputs(copy_root)
            dist = copy_root / "dist"
            dist.mkdir()
            sentinel = dist / "do-not-replace.txt"
            sentinel.write_text("existing output", encoding="utf-8")
            strategy = copy_root / "config/strategy/white.conf"
            strategy.write_text(
                strategy.read_text(encoding="utf-8") + "\n{missing-fragment}\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(copy_root / "main.py")],
                cwd=str(outside),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "existing output")
            self.assertEqual(list(dist.glob("shadowrocket_*.conf")), [])

    def test_unknown_placeholder_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "project"
            self._copy_build_inputs(copy_root)
            strategy = copy_root / "config/strategy/white.conf"
            strategy.write_text(
                strategy.read_text(encoding="utf-8") + "\n{missing-fragment}\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Unknown placeholder"):
                main.render_profiles(copy_root, FIXED_TIME)

    def test_missing_input_fails_fast(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "project"
            self._copy_build_inputs(copy_root)
            (copy_root / "config/rules/proxy.conf").unlink()

            with self.assertRaisesRegex(ValueError, r"Unknown placeholder.*proxy"):
                main.render_profiles(copy_root, FIXED_TIME)

    def test_write_profiles_validates_every_output_before_staging(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            dist = project_root / "dist"
            dist.mkdir()
            sentinel = dist / "keep.txt"
            sentinel.write_text("preserve", encoding="utf-8")

            profiles = main.render_profiles(PROJECT_ROOT, FIXED_TIME)
            profiles["shadowrocket_white.conf"] = profiles["shadowrocket_white.conf"].replace(
                "[Rule]", "[InvalidRule]", 1
            )
            with self.assertRaisesRegex(ValueError, r"\[Rule\]"):
                main.write_profiles(project_root, profiles)

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")
            self.assertEqual(list(dist.glob("shadowrocket_*.conf")), [])

    def test_script_uses_project_paths_when_run_from_outside_repo(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            copy_root = temp_root / "project"
            outside = temp_root / "outside"
            outside.mkdir()
            self._copy_build_inputs(copy_root)

            result = subprocess.run(
                [sys.executable, str(copy_root / "main.py")],
                cwd=str(outside),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            generated = sorted((copy_root / "dist").glob("shadowrocket_*.conf"))
            self.assertEqual(len(generated), 8)

    @staticmethod
    def _copy_build_inputs(destination):
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / "main.py", destination / "main.py")
        shutil.copy2(PROJECT_ROOT / "base.conf", destination / "base.conf")
        shutil.copy2(
            PROJECT_ROOT / "shadowrocket_free.conf",
            destination / "shadowrocket_free.conf",
        )
        shutil.copytree(PROJECT_ROOT / "shadowrocket", destination / "shadowrocket")
        shutil.copytree(PROJECT_ROOT / "config", destination / "config")


if __name__ == "__main__":
    unittest.main()
