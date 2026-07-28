import importlib.util
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("functions.py")
SPEC = importlib.util.spec_from_file_location("copy_update_functions", MODULE_PATH)
copy_update = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(copy_update)


class CopyUpdateTests(unittest.TestCase):
    def make_config(self, source, target, **overrides):
        config = {
            "path_in": str(source),
            "path_out": str(target),
            "path_log": None,
            "if_count": True,
            "copy_workers": 2,
            "delete_workers": 2,
            "report_interval": 60,
        }
        config.update(overrides)
        return config

    def test_renamed_directory_removes_old_and_copies_new(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            new_dir = source / "df004_servo_dog_12dof_全自由度舵机四足狗"
            old_dir = target / "df004_servo_dog_12dof"
            new_dir.mkdir(parents=True)
            old_dir.mkdir(parents=True)
            (new_dir / "new.txt").write_text("new", encoding="utf-8")
            (old_dir / "old.txt").write_text("old", encoding="utf-8")

            result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertTrue(result)
            self.assertFalse(old_dir.exists())
            self.assertEqual(
                (target / new_dir.name / "new.txt").read_text(encoding="utf-8"),
                "new",
            )

    def test_dry_run_reports_but_changes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            stale = target / "stale"
            stale.mkdir(parents=True)
            (source / "new.txt").write_text("new", encoding="utf-8")
            (stale / "old.txt").write_text("old", encoding="utf-8")

            result = copy_update.copy_with_structure(
                self.make_config(source, target, dry_run=True)
            )

            self.assertTrue(result)
            self.assertTrue((stale / "old.txt").exists())
            self.assertFalse((target / "new.txt").exists())

    def test_delete_failure_does_not_stop_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            stale = target / "stale"
            stale.mkdir(parents=True)
            (source / "new.txt").write_text("new", encoding="utf-8")
            (stale / "old.txt").write_text("old", encoding="utf-8")

            with mock.patch.object(
                copy_update, "fs_rmtree", side_effect=PermissionError("locked")
            ):
                result = copy_update.copy_with_structure(
                    self.make_config(source, target)
                )

            self.assertFalse(result)
            self.assertTrue(stale.exists())
            self.assertEqual(
                (target / "new.txt").read_text(encoding="utf-8"),
                "new",
            )

    def test_type_conflict_failure_does_not_stop_sibling_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source_conflict = source / "conflict"
            source_conflict.mkdir(parents=True)
            target.mkdir()
            (source_conflict / "nested.txt").write_text("nested", encoding="utf-8")
            (source / "sibling.txt").write_text("sibling", encoding="utf-8")
            (target / "conflict").write_text("target file", encoding="utf-8")

            with mock.patch.object(
                copy_update, "fs_remove", side_effect=PermissionError("locked")
            ):
                result = copy_update.copy_with_structure(
                    self.make_config(source, target)
                )

            self.assertFalse(result)
            self.assertEqual(
                (target / "sibling.txt").read_text(encoding="utf-8"),
                "sibling",
            )
            self.assertTrue((target / "conflict").is_file())

    def test_delete_failure_is_written_to_only_the_run_log(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            log_dir = root / "logs"
            source.mkdir()
            stale = target / "stale"
            stale.mkdir(parents=True)
            (source / "new.txt").write_text("new", encoding="utf-8")

            with mock.patch.object(
                copy_update, "fs_rmtree", side_effect=PermissionError("locked")
            ):
                result = copy_update.copy_with_structure(
                    self.make_config(source, target, path_log=str(log_dir))
                )

            log_files = list(log_dir.iterdir())
            self.assertFalse(result)
            self.assertEqual(len(log_files), 1)
            self.assertRegex(
                log_files[0].name,
                r"^backup_sync_\d{8}_\d{6}\.log$",
            )
            log_text = log_files[0].read_text(encoding="utf-8")
            self.assertIn("Failed to delete dir:", log_text)
            self.assertIn("locked", log_text)
            self.assertIn("Copying will continue", log_text)
            self.assertIn("Copy finished", log_text)
            self.assertIn("[INCOMPLETE]", log_text)

    def test_readonly_stale_directory_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            stale = target / "stale"
            stale.mkdir(parents=True)
            readonly_file = stale / "git_object"
            readonly_file.write_text("old", encoding="utf-8")
            readonly_file.chmod(stat.S_IREAD)
            (source / "new.txt").write_text("new", encoding="utf-8")

            result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertTrue(result)
            self.assertFalse(stale.exists())
            self.assertTrue((target / "new.txt").is_file())

    def test_readonly_file_created_by_copy2_can_be_deleted_next_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            git_object = source / "git_object"
            git_object.write_text("object", encoding="utf-8")
            git_object.chmod(stat.S_IREAD)

            first_result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )
            copied_object = target / "git_object"
            self.assertTrue(first_result)
            self.assertTrue(copied_object.stat().st_file_attributes & 1)

            git_object.chmod(stat.S_IWRITE)
            git_object.unlink()
            (source / "current.txt").write_text("current", encoding="utf-8")
            second_result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertTrue(second_result)
            self.assertFalse(copied_object.exists())
            self.assertTrue((target / "current.txt").is_file())

    def test_changed_file_is_overwritten_without_predelete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            (source / "data.txt").write_text("new source data", encoding="utf-8")
            (target / "data.txt").write_text("old", encoding="utf-8")

            with mock.patch.object(
                copy_update,
                "fs_remove",
                side_effect=AssertionError("changed file must not be pre-deleted"),
            ):
                result = copy_update.copy_with_structure(
                    self.make_config(source, target)
                )

            self.assertTrue(result)
            self.assertEqual(
                (target / "data.txt").read_text(encoding="utf-8"),
                "new source data",
            )

    def test_failed_atomic_copy_preserves_existing_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            source_file = source / "data.txt"
            target_file = target / "data.txt"
            source_file.write_text("new source data", encoding="utf-8")
            target_file.write_text("old", encoding="utf-8")

            with mock.patch.object(
                copy_update, "fs_copy2", side_effect=OSError("copy failed")
            ):
                result = copy_update.copy_with_structure(
                    self.make_config(source, target)
                )

            self.assertFalse(result)
            self.assertEqual(
                target_file.read_text(encoding="utf-8"),
                "old",
            )
            self.assertEqual(
                list(target.glob("*.backup_tmp")),
                [],
            )

    def test_broken_symbolic_link_is_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            broken_link = source / "latest"
            try:
                os.symlink("missing_target", broken_link)
            except OSError as error:
                self.skipTest(f"Symbolic links are unavailable: {error}")

            result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertTrue(result)
            self.assertFalse((target / "latest").exists())

    def test_empty_source_does_not_clear_nonempty_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            protected = target / "keep.txt"
            protected.write_text("keep", encoding="utf-8")

            result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertFalse(result)
            self.assertEqual(protected.read_text(encoding="utf-8"), "keep")

    def test_target_directory_is_replaced_by_source_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            conflict = target / "same_name"
            conflict.mkdir(parents=True)
            (conflict / "old.txt").write_text("old", encoding="utf-8")
            (source / "same_name").write_text("new file", encoding="utf-8")

            result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertTrue(result)
            self.assertTrue((target / "same_name").is_file())
            self.assertEqual(
                (target / "same_name").read_text(encoding="utf-8"),
                "new file",
            )

    def test_target_file_is_replaced_by_source_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source_dir = source / "same_name"
            source_dir.mkdir(parents=True)
            target.mkdir()
            (source_dir / "new.txt").write_text("new", encoding="utf-8")
            (target / "same_name").write_text("old file", encoding="utf-8")

            result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertTrue(result)
            self.assertTrue((target / "same_name").is_dir())
            self.assertEqual(
                (target / "same_name" / "new.txt").read_text(encoding="utf-8"),
                "new",
            )

    def test_stale_directory_with_long_nested_path_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            stale = target / "stale_project"
            long_dir = stale.joinpath(*(["long_segment_0123456789"] * 12))
            copy_update.fs_makedirs(str(long_dir))
            long_file = long_dir / "old.txt"
            with open(
                copy_update.to_fs_path(str(long_file)),
                "w",
                encoding="utf-8",
            ) as file:
                file.write("old")
            os.chmod(copy_update.to_fs_path(str(long_file)), stat.S_IREAD)
            (source / "current.txt").write_text("new", encoding="utf-8")

            result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertTrue(result)
            self.assertFalse(copy_update.fs_exists(str(stale)))
            self.assertTrue((target / "current.txt").is_file())

    def test_overlapping_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = source / "target"
            source.mkdir()

            result = copy_update.copy_with_structure(
                self.make_config(source, target)
            )

            self.assertFalse(result)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
