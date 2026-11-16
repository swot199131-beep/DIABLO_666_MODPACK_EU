from pathlib import Path
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("diablo_test_main", ROOT / "main.py")
APP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APP)


def fake_wotmod(label="test"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("meta.xml", f"<mod>{label}</mod>")
    return buffer.getvalue()


class InstallerSafetyTests(unittest.TestCase):
    def setUp(self):
        self.installer = APP.DiabloInstaller.__new__(APP.DiabloInstaller)

    def test_safe_relative_paths(self):
        for value in ("mods/2.4.1.1/test.wotmod", "res_mods/2.4.1.1/gui/test.xml"):
            self.assertEqual(self.installer._safe_relative(value).as_posix(), value)
        for value in ("../escape", "C:/Windows/file", "mods/../../escape", "outside/file"):
            with self.assertRaises(ValueError):
                self.installer._safe_relative(value)

    def test_conflict_group_blocks_two_reticles(self):
        self.installer.modules = [
            {"id": "a", "name": "Reticle A", "conflict_groups": ["primary_reticle"]},
            {"id": "b", "name": "Reticle B", "conflict_groups": ["primary_reticle"]},
        ]
        self.installer.checked = {"a": True, "b": True}
        conflicts = self.installer.get_selection_conflicts()
        self.assertTrue(conflicts)
        self.assertIn("primary_reticle", conflicts[0])

    def test_user_import_manifest_and_hash(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "improved_standard_sight_130")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            archive_path = Path(td) / "sight.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("mods/2.4.1.1/center_corners_1.3.0.wotmod", fake_wotmod())
            manifest = self.installer._prepare_local_official_import(module, archive_path, "2.4.1.1")
            self.assertEqual(len(manifest["files"]), 1)
            self.assertEqual(len(manifest["files"][0]["sha256"]), 64)
            package_dir = APP.APP_DATA_DIR / "packages" / module["package_dir"]
            self.assertTrue((package_dir / "manifest.json").is_file())
            shutil.rmtree(package_dir, ignore_errors=True)


    def test_minimap_zoom_import(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "minimap_zoom_15")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            archive_path = Path(td) / "zoom.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("mods/2.4.1.1/minimap_zoom_test.wotmod", fake_wotmod("zoom"))
            manifest = self.installer._prepare_local_official_import(module, archive_path, "2.4.1.1")
            self.assertEqual(len(manifest["files"]), 1)
        shutil.rmtree(APP.APP_DATA_DIR / "packages" / module["package_dir"], ignore_errors=True)

    def test_tank_setup_exporter_imports_optional_menu(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "tank_setup_exporter_020")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            archive_path = Path(td) / "exporter.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("mods/2.4.1.1/gravity.tank_setup_export.2.4.1.1.0.2.0.wotmod", fake_wotmod("exporter"))
                archive.writestr("mods/2.4.1.1/aslain.modmenu_1.0.wotmod", fake_wotmod("menu"))
            manifest = self.installer._prepare_local_official_import(module, archive_path, "2.4.1.1")
            self.assertEqual(len(manifest["files"]), 2)
        shutil.rmtree(APP.APP_DATA_DIR / "packages" / module["package_dir"], ignore_errors=True)

    def test_existing_optional_menu_is_not_duplicated(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "wreck_colours_100")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            installed = Path(td) / "mods" / "2.4.1.1" / "aslain.modmenu_1.0.wotmod"
            installed.parent.mkdir(parents=True)
            installed.write_bytes(fake_wotmod("already-installed-menu"))
            archive_path = Path(td) / "wreck.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("mods/2.4.1.1/gravity.wreck_colours.2.4.1.1.1.0.0.wotmod", fake_wotmod("wreck"))
                archive.writestr("mods/2.4.1.1/aslain.modmenu_1.0.wotmod", fake_wotmod("duplicate-menu"))
            manifest = self.installer._prepare_local_official_import(module, archive_path, "2.4.1.1")
            self.assertEqual(len(manifest["files"]), 1)
            self.assertIn("wreck_colours", manifest["files"][0]["source"])
        shutil.rmtree(APP.APP_DATA_DIR / "packages" / module["package_dir"], ignore_errors=True)


    def test_failed_reimport_preserves_previous_valid_package(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "improved_standard_sight_130")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            package_dir = APP.APP_DATA_DIR / "packages" / module["package_dir"]
            package_dir.mkdir(parents=True, exist_ok=True)
            old_manifest = package_dir / "manifest.json"
            old_manifest.write_text('{"previous":"valid"}', encoding="utf-8")
            bad_archive = Path(td) / "wrong.zip"
            with zipfile.ZipFile(bad_archive, "w") as archive:
                archive.writestr("mods/2.4.1.1/not_the_selected_mod.wotmod", fake_wotmod("wrong"))
            with self.assertRaises(ValueError):
                self.installer._prepare_local_official_import(module, bad_archive, "2.4.1.1")
            self.assertTrue(old_manifest.is_file())
            self.assertIn("previous", old_manifest.read_text(encoding="utf-8"))
        shutil.rmtree(APP.APP_DATA_DIR / "packages" / module["package_dir"], ignore_errors=True)

    def test_gunner_hud_import(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "gunner_hud_061")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            # Use the exact file pattern from the current WGMods release.
            archive_path = Path(td) / "maksforge.gunner_hud_0.6.1.wotmod"
            archive_path.write_bytes(fake_wotmod("gunner"))
            manifest = self.installer._prepare_local_official_import(module, archive_path, "2.4.1.1")
            self.assertEqual(len(manifest["files"]), 1)
        shutil.rmtree(APP.APP_DATA_DIR / "packages" / module["package_dir"], ignore_errors=True)

    def test_battlestats_import(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "battlestats_custix_154")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            archive_path = Path(td) / "battlestats.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("mods/2.4.1.1/custix.battlestats_1.5.4.wotmod", fake_wotmod("stats"))
            manifest = self.installer._prepare_local_official_import(module, archive_path, "2.4.1.1")
            self.assertEqual(len(manifest["files"]), 1)
        shutil.rmtree(APP.APP_DATA_DIR / "packages" / module["package_dir"], ignore_errors=True)


    def test_version_xml_parser_reads_mod_compatibility_version(self):
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            (self.installer.game_path / "version.xml").write_text(
                "<root><version>v2.4.1.1</version></root>", encoding="utf-8"
            )
            self.assertEqual(self.installer._game_version(), "2.4.1.1")

    def test_wotmod_with_traversal_path_is_rejected(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "improved_standard_sight_130")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, "w") as archive:
                archive.writestr("../escape.txt", "bad")
            archive_path = Path(td) / "center_corners_1.3.0.wotmod"
            archive_path.write_bytes(inner.getvalue())
            with self.assertRaises(ValueError):
                self.installer._prepare_local_official_import(module, archive_path, "2.4.1.1")
        shutil.rmtree(APP.APP_DATA_DIR / "packages" / module["package_dir"], ignore_errors=True)



    def test_windows_setup_project_has_expected_output_and_per_user_install(self):
        iss = (ROOT / "installer" / "DIABLO_666_MODPACK_EU.iss").read_text(encoding="utf-8")
        self.assertIn("OutputBaseFilename=DIABLO_666_MODPACK_EU_Setup_v{#MyAppVersion}", iss)
        self.assertIn('#define MyAppVersion "0.6.1"', iss)
        self.assertIn("PrivilegesRequired=lowest", iss)
        self.assertIn("DefaultDirName={localappdata}", iss)
        self.assertIn("DIABLO_666_MODPACK_EU.exe", iss)
        self.assertTrue((ROOT / "assets" / "diablo_icon.ico").is_file())

    def test_windows_ci_builds_inno_setup_and_publishes_checksum(self):
        workflow = (ROOT / ".github" / "workflows" / "build-windows.yml").read_text(encoding="utf-8")
        self.assertIn("runs-on: windows-latest", workflow)
        self.assertIn("choco install innosetup", workflow)
        self.assertIn("DIABLO_666_MODPACK_EU_Setup_v0.6.1.exe", workflow)
        self.assertIn("Get-FileHash", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)


    def test_reconcile_removes_obsolete_diablo_file_and_restores_backup(self):
        with tempfile.TemporaryDirectory() as td:
            old_app_data = APP.APP_DATA_DIR
            APP.APP_DATA_DIR = Path(td) / "appdata"
            game = Path(td) / "game"
            try:
                self.installer.game_path = game
                target = game / "mods" / "2.4.1.1" / "old.wotmod"
                target.parent.mkdir(parents=True)
                target.write_bytes(b"diablo version")
                backup = APP.APP_DATA_DIR / "backups" / "original.wotmod"
                backup.parent.mkdir(parents=True)
                backup.write_bytes(b"original version")
                state = {"files": {
                    "mods/2.4.1.1/old.wotmod": {
                        "backup": "backups/original.wotmod",
                        "installed_sha256": APP.hashlib.sha256(b"diablo version").hexdigest(),
                        "modules": ["old_module"]
                    }
                }}
                removed, skipped = self.installer._reconcile_obsolete_files(state, {})
                self.assertEqual(removed, 1)
                self.assertEqual(skipped, [])
                self.assertEqual(target.read_bytes(), b"original version")
                self.assertEqual(state["files"], {})
            finally:
                APP.APP_DATA_DIR = old_app_data

    def test_reconcile_keeps_shared_file_for_selected_module(self):
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td) / "game"
            target = self.installer.game_path / "mods" / "2.4.1.1" / "shared.wotmod"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"managed")
            state = {"files": {
                "mods/2.4.1.1/shared.wotmod": {
                    "backup": None,
                    "installed_sha256": APP.hashlib.sha256(b"managed").hexdigest(),
                    "modules": ["old_module", "selected_module"]
                }
            }}
            removed, skipped = self.installer._reconcile_obsolete_files(
                state, {"mods/2.4.1.1/shared.wotmod": ["selected_module"]}
            )
            self.assertEqual(removed, 0)
            self.assertEqual(skipped, [])
            self.assertEqual(state["files"]["mods/2.4.1.1/shared.wotmod"]["modules"], ["selected_module"])
            self.assertTrue(target.is_file())

    def test_reconcile_never_deletes_file_changed_by_other_tool(self):
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td) / "game"
            target = self.installer.game_path / "mods" / "2.4.1.1" / "changed.wotmod"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"replaced by another modpack")
            state = {"files": {
                "mods/2.4.1.1/changed.wotmod": {
                    "backup": None,
                    "installed_sha256": APP.hashlib.sha256(b"original diablo bytes").hexdigest(),
                    "modules": ["old_module"]
                }
            }}
            removed, skipped = self.installer._reconcile_obsolete_files(state, {})
            self.assertEqual(removed, 0)
            self.assertEqual(len(skipped), 1)
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_bytes(), b"replaced by another modpack")
            self.assertEqual(state["files"], {})

    def test_reconcile_stops_if_selected_destination_was_modified_externally(self):
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td) / "game"
            target = self.installer.game_path / "mods" / "2.4.1.1" / "changed.wotmod"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"other tool")
            state = {"files": {
                "mods/2.4.1.1/changed.wotmod": {
                    "backup": None,
                    "installed_sha256": APP.hashlib.sha256(b"diablo old").hexdigest(),
                    "modules": ["old_module"]
                }
            }}
            with self.assertRaises(RuntimeError):
                self.installer._reconcile_obsolete_files(
                    state, {"mods/2.4.1.1/changed.wotmod": ["new_module"]}
                )
            self.assertEqual(target.read_bytes(), b"other tool")


    def test_profile_handlers_exist(self):
        self.assertTrue(callable(getattr(APP.DiabloInstaller, "save_profile", None)))
        self.assertTrue(callable(getattr(APP.DiabloInstaller, "load_profile", None)))

    def test_profile_name_normalization(self):
        self.assertEqual(APP.normalize_profile_name("  Снайпер / EU!  "), "Снайпер  EU")
        with self.assertRaises(ValueError):
            APP.normalize_profile_name("...")

    def test_profile_payload_validates_known_unique_modules(self):
        profile = {"schema_version": 1, "selected_module_ids": ["reticle_a", "minimap"]}
        self.assertEqual(
            APP.validate_profile_payload(profile, {"reticle_a", "minimap"}),
            {"reticle_a", "minimap"}
        )

    def test_profile_payload_rejects_unknown_and_duplicate_modules(self):
        with self.assertRaises(ValueError):
            APP.validate_profile_payload(
                {"schema_version": 1, "selected_module_ids": ["unknown"]},
                {"reticle_a"}
            )
        with self.assertRaises(ValueError):
            APP.validate_profile_payload(
                {"schema_version": 1, "selected_module_ids": ["reticle_a", "reticle_a"]},
                {"reticle_a"}
            )

    def test_wrong_client_version_is_rejected(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        module = next(m for m in catalog["modules"] if m["id"] == "improved_standard_sight_130")
        with tempfile.TemporaryDirectory() as td:
            self.installer.game_path = Path(td)
            archive_path = Path(td) / "sight.wotmod"
            archive_path.write_bytes(fake_wotmod())
            with self.assertRaises(ValueError):
                self.installer._prepare_local_official_import(module, archive_path, "2.4.1.0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
