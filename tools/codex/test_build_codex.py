"""Regression tests for the Codex skills-tree generator."""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("build_codex.py")
SPEC = importlib.util.spec_from_file_location("build_codex", MODULE_PATH)
build_codex = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_codex)


class OutputPathValidationTests(unittest.TestCase):
    """Ensure generation cannot recursively delete protected paths."""

    def test_rejects_repository_root_and_paths_inside_it(self):
        candidates = [
            build_codex.ROOT,
            build_codex.ROOT / "skills",
            build_codex.ROOT / "scratch",
        ]

        for candidate in candidates:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                build_codex.validate_output_path(candidate)

    def test_rejects_repository_ancestors(self):
        for candidate in build_codex.ROOT.parents:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                build_codex.validate_output_path(candidate)

    def test_rejects_codex_home_and_paths_inside_it(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            codex_home = Path(temporary_dir) / "codex-home"
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
                for candidate in [codex_home, codex_home / "skills"]:
                    with (
                        self.subTest(candidate=candidate),
                        self.assertRaises(ValueError),
                    ):
                        build_codex.validate_output_path(candidate)

    def test_accepts_external_scratch_directory(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            candidate = Path(temporary_dir) / "generated"

            self.assertEqual(
                build_codex.validate_output_path(candidate),
                candidate.resolve(),
            )

    def test_refuses_to_overwrite_unowned_existing_directory(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            candidate = Path(temporary_dir) / "documents"
            candidate.mkdir()
            sentinel = candidate / "keep.txt"
            sentinel.write_text("user data")

            with self.assertRaises(ValueError):
                build_codex.prepare_output_directory(candidate)

            self.assertEqual(sentinel.read_text(), "user data")

    def test_overwrites_directory_with_generator_marker(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            candidate = Path(temporary_dir) / "generated"
            candidate.mkdir()
            marker = candidate / build_codex.GENERATED_MARKER
            marker.write_text(f"{build_codex.ROOT}\n")
            stale_file = candidate / "stale.txt"
            stale_file.write_text("old output")

            build_codex.prepare_output_directory(candidate)

            self.assertFalse(stale_file.exists())
            self.assertEqual(marker.read_text(), f"{build_codex.ROOT}\n")


class ReportValidationTests(unittest.TestCase):
    """Ensure incomplete folding is a build failure."""

    def test_missing_fold_targets_are_fatal(self):
        report = {
            "folded": [],
            "relocated": [],
            "missing_targets": ["skills/missing/SKILL.md"],
            "errors": [],
        }

        self.assertTrue(build_codex.report_has_failures(report))

    def test_complete_report_is_successful(self):
        report = {
            "folded": ["agents/example.md"],
            "relocated": [],
            "missing_targets": [],
            "errors": [],
        }

        self.assertFalse(build_codex.report_has_failures(report))

    def test_main_exits_nonzero_when_a_fold_target_is_missing(self):
        def record_missing_target(_fold_map, _out_root, report):
            report["missing_targets"].append("skills/missing/SKILL.md")

        with (
            tempfile.TemporaryDirectory() as temporary_dir,
            mock.patch.object(
                sys,
                "argv",
                ["build_codex.py", "--out", str(Path(temporary_dir) / "output")],
            ),
            mock.patch.object(build_codex, "copy_skills_tree"),
            mock.patch.object(build_codex, "fold_agents", record_missing_target),
            mock.patch.object(build_codex, "fold_commands"),
            mock.patch.object(
                build_codex, "load_fold_map", return_value={"excluded": []}
            ),
            self.assertRaises(SystemExit) as raised,
        ):
            build_codex.main()

        self.assertEqual(raised.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
