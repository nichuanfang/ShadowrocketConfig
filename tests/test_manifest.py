import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import main  # noqa: E402
from shadowrocket.manifest import ManifestError, load_profiles  # noqa: E402
from shadowrocket.release import build_release_plan, write_release_plan  # noqa: E402


FIXED_TIME = datetime(2026, 1, 2, 3, 4, 5)


class ManifestTests(unittest.TestCase):
    def test_manifest_preserves_ids_and_release_order(self):
        definitions = load_profiles(PROJECT_ROOT)

        self.assertEqual(
            [definition.id for definition in definitions],
            [
                "free",
                "black",
                "black_ad",
                "black_accelerate",
                "black_accelerate_ad",
                "white",
                "white_ad",
                "white_accelerate",
                "white_accelerate_ad",
            ],
        )
        self.assertEqual(definitions[0].artifact_relative_path(), Path("shadowrocket_free.conf"))
        self.assertEqual(
            definitions[1].artifact_relative_path(),
            Path("dist/shadowrocket_black.conf"),
        )

    def test_new_template_is_discovered_without_python_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_project(root)
            (root / "config/strategy/minimal.conf").write_text(
                "{direct}\nFINAL,PROXY\n", encoding="utf-8"
            )
            manifest = root / "config/profiles.toml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8")
                + '\n[[profiles]]\nid = "minimal"\ntemplate = "config/strategy/minimal.conf"\n',
                encoding="utf-8",
            )

            profiles = main.render_profiles(root, FIXED_TIME)

            self.assertIn("shadowrocket_minimal.conf", profiles)
            self.assertIn("[Rule]", profiles["shadowrocket_minimal.conf"])
            self.assertTrue(profiles["shadowrocket_minimal.conf"].endswith("\n"))

    def test_local_only_profile_is_not_published(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_project(root)
            manifest = root / "config/profiles.toml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8")
                + '\n[[profiles]]\nid = "local"\ntemplate = "config/strategy/white.conf"\n',
                encoding="utf-8",
            )
            main.write_profiles(root, main.render_profiles(root, FIXED_TIME))

            definitions = load_profiles(root)
            self.assertIsNone(definitions[-1].gist_secret)
            plan = build_release_plan(root)
            self.assertNotIn("local", {item["id"] for item in plan["items"]})

    def test_release_plan_covers_existing_gists_in_order(self):
        plan = build_release_plan(PROJECT_ROOT)

        self.assertEqual(plan["version"], 1)
        self.assertEqual(
            [(item["id"], item["gist_secret"]) for item in plan["items"]],
            [
                ("free", "FREE_GIST_ID"),
                ("black", "BLACK_GIST_ID"),
                ("black_ad", "BLACK_AD_GIST_ID"),
                ("black_accelerate", "BLACK_ACCELERATE_GIST_ID"),
                ("black_accelerate_ad", "BLACK_ACCELERATE_AD_GIST_ID"),
                ("white", "WHITE_GIST_ID"),
                ("white_ad", "WHITE_AD_GIST_ID"),
                ("white_accelerate", "WHITE_ACCELERATE_GIST_ID"),
                ("white_accelerate_ad", "WHITE_ACCELERATE_AD_GIST_ID"),
            ],
        )
        self.assertTrue(all(item["path"].endswith(".conf") for item in plan["items"]))

    def test_duplicate_ids_and_secret_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_project(root)
            manifest = root / "config/profiles.toml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8")
                + '\n[[profiles]]\nid = "black"\ntemplate = "config/strategy/white.conf"\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ManifestError, "Duplicate profile id"):
                load_profiles(root)

            manifest.write_text(
                manifest.read_text(encoding="utf-8").replace(
                    'id = "black"\ntemplate',
                    'id = "duplicate"\ntemplate',
                    1,
                ).replace(
                    'gist_secret = "FREE_GIST_ID"',
                    'gist_secret = "BLACK_GIST_ID"',
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ManifestError, "Duplicate gist_secret"):
                load_profiles(root)

    def test_manifest_rejects_paths_outside_project_and_bad_shapes(self):
        cases = {
            "escape": '\n[[profiles]]\nid = "escape"\ntemplate = "../outside.conf"\n',
            "both": '\n[[profiles]]\nid = "both"\ntemplate = "config/strategy/white.conf"\nsource = "shadowrocket_free.conf"\n',
            "neither": '\n[[profiles]]\nid = "neither"\n',
            "source": '\n[[profiles]]\nid = "source"\nsource = "dist/release-plan.json"\n',
            "template": '\n[[profiles]]\nid = "template"\ntemplate = "config/strategy/white.txt"\n',
            "secret": '\n[[profiles]]\nid = "secret"\ntemplate = "config/strategy/white.conf"\ngist_secret = "lowercase"\n',
            "field": '\n[[profiles]]\nid = "field"\ntemplate = "config/strategy/white.conf"\nunknown = "value"\n',
        }
        for label, addition in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                self._copy_project(root)
                manifest = root / "config/profiles.toml"
                manifest.write_text(manifest.read_text(encoding="utf-8") + addition, encoding="utf-8")
                with self.assertRaises(ManifestError):
                    load_profiles(root)

    def test_release_requires_every_artifact_before_writing_plan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_project(root)
            (root / "shadowrocket_free.conf").unlink()

            with self.assertRaisesRegex(FileNotFoundError, "shadowrocket_free.conf"):
                build_release_plan(root)
            self.assertFalse((root / "dist/release-plan.json").exists())

    def test_static_module_can_be_released(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._copy_project(root)
            shutil.copytree(PROJECT_ROOT / "module", root / "module")
            manifest = root / "config/profiles.toml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8")
                + '\n[[profiles]]\nid = "youtube_ad"\nsource = "module/YouTubeAd.sgmodule"\ngist_secret = "YOUTUBE_AD_GIST_ID"\n',
                encoding="utf-8",
            )
            main.write_profiles(root, main.render_profiles(root, FIXED_TIME))

            item = build_release_plan(root)["items"][-1]

            self.assertEqual(
                item,
                {
                    "id": "youtube_ad",
                    "path": "module/YouTubeAd.sgmodule",
                    "gist_file": "YouTubeAd.sgmodule",
                    "gist_secret": "YOUTUBE_AD_GIST_ID",
                },
            )

    def test_release_plan_is_json_utf8_and_atomic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = {"version": 1, "items": [{"id": "免费", "path": "x.conf"}]}
            destination = write_release_plan(root, plan)

            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), plan)
            self.assertEqual(list(destination.parent.glob(".release-plan.json.*")), [])

    @staticmethod
    def _copy_project(destination):
        destination.mkdir(parents=True, exist_ok=True)
        for name in ("main.py", "base.conf", "shadowrocket_free.conf"):
            shutil.copy2(PROJECT_ROOT / name, destination / name)
        shutil.copytree(PROJECT_ROOT / "shadowrocket", destination / "shadowrocket")
        shutil.copytree(PROJECT_ROOT / "config", destination / "config")


if __name__ == "__main__":
    unittest.main()
