"""Behavioral tests for selected-card lifecycle integrity validation."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional, Union
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[1]
CHECKER = REPOSITORY / "skills/zeno/scripts/check_lifecycle.py"
CARD_TYPES = {
    "Epic": ("EPIC", "epics"),
    "Feature": ("FEAT", "features"),
    "Story": ("STORY", "stories"),
    "Task": ("TASK", "tasks"),
    "SubTask": ("SUBTASK", "subtasks"),
}


def evidence(
    identifier: str = "E-check",
    result: str = "pass",
    required: str = "yes",
    kind: str = "check",
    claim: str = "The accepted behavior works.",
    extra: str = "",
) -> str:
    """Build one canonical evidence record without running its command."""
    return (
        f"### {identifier}\n"
        f"- Claim: {claim}\n"
        f"- Required: {required}\n"
        f"- Kind: {kind}\n"
        f"- Result: {result}\n"
        "- Evidence: `python -m unittest` -> exit 0; behavior observed.\n"
        "- Revision: working-tree-snapshot-1\n"
        "- Environment: isolated unittest fixture\n"
        "- Owner: independent-reviewer\n"
        f"{extra}\n"
    )


class LifecycleCliTests(unittest.TestCase):
    """Exercise the installed-style CLI against disposable card hierarchies."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / ".zeno"
        self.root.mkdir()

    def card(
        self,
        kind: str = "Task",
        slug: str = "sample",
        status: str = "development",
        proof: str = "",
        extra: str = "",
        decisions: str = "",
    ) -> Path:
        """Write a complete card skeleton, optionally with closure evidence."""
        prefix, directory = CARD_TYPES[kind]
        path = self.root / "docs" / directory / f"{prefix}-{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        scope = ""
        if kind in {"Epic", "Feature", "Story"}:
            scope = (
                "## Scope\n"
                "- **Problem:** Behavior needs improvement.\n"
                "- **Approach:** Make the accepted scoped change.\n"
                "- **Done looks like:** Accepted behavior is observed.\n\n"
            )
        outcome = (
            "Delivered and verified accepted behavior."
            if status == "closed"
            else ""
        )
        path.write_text(
            f"# {kind}: {slug}\n\n"
            "**Goal:** Deliver the accepted behavior.\n"
            f"**Status:** {status}\n"
            "**Owner:** contributor\n"
            "**Updated:** 2026-11-15\n\n"
            f"{scope}"
            "## Description\nImplement the bounded change.\n\n"
            f"{extra}\n"
            f"## Proof\n{proof}\n"
            f"## Decisions\n{decisions}\n"
            f"## Outcome\n{outcome}\n",
            encoding="utf-8",
        )
        return path

    def story(self, status: str = "testing", proof: str = "") -> Path:
        """Write a route-ready Story with its closed documentation Task."""
        self.card("Task", "docs", "closed", evidence())
        return self.card(
            "Story",
            "story",
            status,
            proof,
            "## Acceptance criteria (ATDD)\n"
            "- The behavior is observable.\n\n"
            "## Scenarios (BDD)\n"
            "### Scenario: Accepted behavior\n"
            "- **Given** the accepted state\n"
            "- **When** the operation runs\n"
            "- **Then** the accepted behavior is observed\n\n"
            "## Task list (breakdown)\n"
            "- [x] TASK-docs [documentation] -> `../tasks/TASK-docs.md`\n",
        )

    def run_card(
        self, path: Path, *arguments: str
    ) -> subprocess.CompletedProcess:
        """Invoke the CLI without a shell or bytecode writes."""
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--json", *arguments],
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
            check=False,
        )

    def assert_result(
        self,
        path: Path,
        result: str,
        *arguments: str,
    ) -> dict:
        """Assert the machine result, exit status and integrity-only scope."""
        run = self.run_card(path, *arguments)
        expected = {"pass": 0, "fail": 1, "blocked": 2}[result]
        self.assertEqual(run.returncode, expected, run.stderr or run.stdout)
        try:
            report = json.loads(run.stdout)
        except json.JSONDecodeError:
            self.fail(f"Expected a JSON report, got: {run.stdout!r}")
        self.assertEqual(report["result"], result)
        self.assertIn("card integrity only", report["scope"].lower())
        self.assertIsInstance(report["path_safety"], str)
        return report

    def test_open_card_allows_empty_proof_and_outcome(self) -> None:
        self.assert_result(self.card(), "pass")

    def test_route_can_pass_before_review_proof_exists(self) -> None:
        path = self.story()
        self.assert_result(path, "pass", "--gate", "route")
        self.assert_result(path, "blocked", "--gate", "review")

    def test_closed_story_and_children_pass_review(self) -> None:
        self.assert_result(
            self.story("closed", evidence()), "pass", "--gate", "review"
        )

    def test_required_nonpassing_evidence_prevents_review(self) -> None:
        for state, verdict in [
            ("fail", "fail"),
            ("blocked", "blocked"),
            ("not_run", "blocked"),
        ]:
            with self.subTest(state=state):
                self.assert_result(
                    self.card(proof=evidence(result=state)),
                    verdict,
                    "--gate",
                    "review",
                )

    def test_optional_failed_recommendation_does_not_veto(self) -> None:
        proof = evidence() + evidence("E-advice", "fail", "no")
        self.assert_result(self.card(proof=proof), "pass", "--gate", "review")

    def test_not_applicable_needs_a_reason(self) -> None:
        self.assert_result(
            self.card(proof=evidence(result="not_applicable")), "fail"
        )
        proof = evidence(
            result="not_applicable", extra="- Reason: Scope excludes it."
        )
        self.assert_result(self.card(proof=proof), "pass", "--gate", "review")

    def test_independent_review_cannot_be_assumed(self) -> None:
        path = self.card(proof=evidence())
        self.assert_result(
            path, "blocked", "--gate", "review", "--require-review"
        )
        path.write_text(
            path.read_text().replace(
                "## Decisions",
                evidence("E-review", kind="review") + "## Decisions",
            ),
            encoding="utf-8",
        )
        self.assert_result(
            path, "pass", "--gate", "review", "--require-review"
        )

    def test_not_applicable_review_is_not_completed_independent_review(
        self,
    ) -> None:
        proof = evidence() + evidence(
            "E-review",
            "not_applicable",
            kind="review",
            extra="- Reason: Unavailable.",
        )
        self.assert_result(
            self.card(proof=proof),
            "blocked",
            "--gate",
            "review",
            "--require-review",
        )

    def test_superseded_failure_remains_history_without_veto(self) -> None:
        proof = evidence("E-old", "fail") + evidence(
            "E-new", extra="- Supersedes: E-old"
        )
        self.assert_result(self.card(proof=proof), "pass", "--gate", "review")

    def test_unrelated_success_cannot_supersede_another_claim(self) -> None:
        proof = evidence("E-old", "fail") + evidence(
            "E-new",
            claim="An unrelated behavior works.",
            extra="- Supersedes: E-old",
        )
        self.assert_result(self.card(proof=proof), "fail")

    def test_supersession_cannot_remove_a_required_failure(self) -> None:
        proof = evidence("E-old", "fail") + evidence(
            "E-new", required="no", extra="- Supersedes: E-old"
        )
        proof += evidence("E-unrelated", claim="An unrelated check passes.")
        self.assert_result(self.card(proof=proof), "fail", "--gate", "review")

    def test_supersession_cannot_change_review_into_check(self) -> None:
        proof = evidence("E-old", "blocked", kind="review") + evidence(
            "E-new", extra="- Supersedes: E-old"
        )
        self.assert_result(self.card(proof=proof), "fail", "--gate", "review")

    def test_missing_or_cyclic_supersession_fails(self) -> None:
        for proof in [
            evidence(extra="- Supersedes: E-missing"),
            evidence("E-one", extra="- Supersedes: E-two")
            + evidence("E-two", extra="- Supersedes: E-one"),
        ]:
            with self.subTest(proof=proof):
                self.assert_result(self.card(proof=proof), "fail")

    def test_duplicate_evidence_ids_and_fields_fail(self) -> None:
        for proof in [
            evidence() + evidence(),
            evidence(extra="- Result: fail"),
        ]:
            with self.subTest(proof=proof):
                self.assert_result(self.card(proof=proof), "fail")

    def test_invalid_result_and_status_fail(self) -> None:
        self.assert_result(self.card(status="approved"), "fail")
        self.assert_result(
            self.card(proof=evidence(result="probably")), "fail"
        )

    def test_closed_card_requires_proof_and_outcome(self) -> None:
        self.assert_result(self.card(status="closed"), "blocked")
        path = self.card(status="closed", proof=evidence())
        path.write_text(
            path.read_text().replace(
                "Delivered and verified accepted behavior.", "<what shipped>"
            )
        )
        self.assert_result(path, "fail")

    def test_required_sections_and_scope_fields_cannot_be_omitted(
        self,
    ) -> None:
        for missing in [
            "## Scope",
            "## Proof",
            "- **Done looks like:** Accepted behavior is observed.",
        ]:
            path = self.story()
            path.write_text(path.read_text().replace(missing, ""))
            with self.subTest(missing=missing):
                self.assert_result(path, "fail")

    def test_comments_and_fences_do_not_supply_required_metadata(self) -> None:
        for wrapper in [
            "<!--\n{}\n-->",
            "```markdown\n{}\n```",
            "~~~\n{}\n~~~",
        ]:
            path = self.card()
            path.write_text(
                path.read_text().replace(
                    "**Owner:** contributor",
                    wrapper.format("**Owner:** contributor"),
                )
            )
            with self.subTest(wrapper=wrapper):
                self.assert_result(path, "fail")

    def test_indented_code_cannot_supply_owner(self) -> None:
        for owner in (
            "    **Owner:** contributor",
            "\t**Owner:** contributor",
            "    ```markdown\n    **Owner:** contributor\n    ```",
        ):
            path = self.card()
            path.write_text(
                path.read_text().replace("**Owner:** contributor", owner),
                encoding="utf-8",
            )
            with self.subTest(owner=owner):
                self.assert_result(path, "fail")

    def test_indented_code_cannot_supply_proof_fields(self) -> None:
        record = evidence().splitlines()
        proof = (
            record[0] + "\n" + "\n".join("    " + line for line in record[1:])
        )
        self.assert_result(self.card(proof=proof), "fail", "--gate", "review")

    def test_comment_openers_inside_examples_do_not_hide_real_metadata(
        self,
    ) -> None:
        for example in (
            "```html\n<!--\n```\n",
            "    <!--\n",
        ):
            path = self.card()
            path.write_text(
                path.read_text().replace("**Goal:**", example + "**Goal:**"),
                encoding="utf-8",
            )
            with self.subTest(example=example):
                self.assert_result(path, "pass")

    def test_canonical_section_aliases_are_duplicates(self) -> None:
        for duplicate in (
            "## Proof (historical)\n" + evidence("E-hidden", "fail"),
            (
                "## Scope (historical)\n"
                "- **Problem:** Another problem.\n"
                "- **Approach:** Another approach.\n"
                "- **Done looks like:** Another outcome.\n"
            ),
            (
                "## Task list (alternate)\n"
                "- [x] [documentation] `../tasks/TASK-docs.md`\n"
            ),
        ):
            path = self.story(proof=evidence())
            path.write_text(path.read_text() + duplicate, encoding="utf-8")
            with self.subTest(duplicate=duplicate):
                self.assert_result(path, "fail", "--gate", "review")

    def test_markdown_wrappers_do_not_make_placeholders_meaningful(
        self,
    ) -> None:
        for replacement in ("`TODO`", "_TODO_", "- [x] <observable behavior>"):
            path = self.card(status="closed", proof=evidence())
            path.write_text(
                path.read_text().replace(
                    "Delivered and verified accepted behavior.", replacement
                ),
                encoding="utf-8",
            )
            with self.subTest(replacement=replacement):
                self.assert_result(path, "fail", "--gate", "review")
        proof = evidence().replace(
            "`python -m unittest` -> exit 0; behavior observed.", "`TODO`"
        )
        self.assert_result(self.card(proof=proof), "fail", "--gate", "review")

    def test_fenced_proof_cannot_satisfy_review(self) -> None:
        proof = f"```markdown\n{evidence()}\n```"
        self.assert_result(
            self.card(proof=proof), "blocked", "--gate", "review"
        )

    def test_missing_child_is_blocked(self) -> None:
        path = self.story()
        (self.root / "docs/tasks/TASK-docs.md").unlink()
        self.assert_result(path, "blocked", "--gate", "route")

    def test_unchecked_child_blocks_review(self) -> None:
        path = self.story(proof=evidence())
        path.write_text(path.read_text().replace("- [x] TASK", "- [ ] TASK"))
        self.assert_result(path, "blocked", "--gate", "review")

    def test_child_type_and_card_title_must_match(self) -> None:
        path = self.story()
        path.write_text(
            path.read_text().replace(
                "../tasks/TASK-docs.md", "../stories/STORY-story.md"
            )
        )
        self.assert_result(path, "fail")
        path = self.card()
        path.write_text(path.read_text().replace("# Task:", "# Feature:"))
        self.assert_result(path, "fail")

    def test_wrong_child_type_is_rejected_before_descending(self) -> None:
        path = self.story()
        self.card(
            "Feature",
            "wrong",
            extra=(
                "## Story list (FDD)\n"
                "- [x] [Unavailable](../stories/STORY-missing.md)\n"
            ),
        )
        path.write_text(
            path.read_text().replace(
                "../tasks/TASK-docs.md", "../features/FEAT-wrong.md"
            ),
            encoding="utf-8",
        )
        report = self.assert_result(path, "fail")
        self.assertEqual(len(report["checked_cards"]), 2)
        self.assertFalse(
            any(item["result"] == "blocked" for item in report["findings"])
        )

    def test_child_escape_and_symlink_escape_fail(self) -> None:
        outside = Path(self.scratch.name) / "TASK-outside.md"
        outside.write_text("This must not be read.", encoding="utf-8")
        path = self.story()
        path.write_text(
            path.read_text().replace(
                "../tasks/TASK-docs.md", "../../../TASK-outside.md"
            )
        )
        self.assert_result(path, "fail")
        path = self.story()
        child = self.root / "docs/tasks/TASK-docs.md"
        child.unlink()
        try:
            child.symlink_to(outside)
        except OSError:
            return
        self.assert_result(path, "fail")

    def test_trailing_documentation_marker_is_required(self) -> None:
        path = self.story()
        path.write_text(path.read_text().replace("[documentation]", ""))
        self.assert_result(path, "fail", "--gate", "route")

    def test_malformed_utf8_is_a_reported_failure(self) -> None:
        path = self.card()
        path.write_bytes(b"\xff")
        self.assert_result(path, "fail")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO needs POSIX")
    def test_fifo_card_is_rejected_without_blocking(self) -> None:
        path = self.card()
        path.unlink()
        os.mkfifo(path)
        self.assert_result(path, "fail")

    def test_required_fail_takes_precedence_over_blocked(self) -> None:
        proof = evidence("E-failed", "fail") + evidence("E-missing", "not_run")
        report = self.assert_result(
            self.card(proof=proof), "fail", "--gate", "review"
        )
        self.assertTrue(
            any(i["result"] == "blocked" for i in report["findings"])
        )

    def test_required_blocker_remains_until_explicitly_superseded(
        self,
    ) -> None:
        proof = evidence(
            "E-blocker", "blocked", claim="Required review is complete."
        )
        proof += evidence("E-unrelated", claim="Behavioral tests pass.")
        self.assert_result(
            self.card(proof=proof),
            "blocked",
            "--gate",
            "review",
        )

    def test_selected_card_does_not_scan_unrelated_legacy_cards(self) -> None:
        path = self.card()
        legacy = self.root / "docs/archive/old.md"
        legacy.parent.mkdir()
        legacy.write_text("invalid legacy content", encoding="utf-8")
        self.assert_result(path, "pass")

    def test_evidence_commands_are_never_executed_and_cards_are_unchanged(
        self,
    ) -> None:
        marker = Path(self.scratch.name) / "must-not-exist"
        proof = evidence().replace("`python -m unittest`", f"`touch {marker}`")
        path = self.card(proof=proof)
        before = path.read_bytes()
        self.assert_result(path, "pass", "--gate", "review")
        self.assertFalse(marker.exists())
        self.assertEqual(path.read_bytes(), before)

    def test_explicit_root_works_without_named_zeno_directory(self) -> None:
        path = self.card()
        renamed = self.root.with_name("cards")
        self.root.rename(renamed)
        path = renamed / path.relative_to(self.root)
        self.assert_result(path, "pass", "--root", str(renamed))

    def test_text_output_also_states_integrity_only_scope(self) -> None:
        run = subprocess.run(
            [sys.executable, str(CHECKER), str(self.card())],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("card integrity only", run.stdout.lower())

    def test_source_templates_provide_required_sections(self) -> None:
        for kind in CARD_TYPES:
            template = (
                REPOSITORY
                / "skills/zeno/references"
                / f"{kind.lower()}-template.md"
            )
            text = template.read_text(encoding="utf-8")
            with self.subTest(kind=kind):
                self.assertIn("**Owner:**", text)
                self.assertIn("## Proof", text)
                if kind in {"Epic", "Feature", "Story"}:
                    self.assertIn("## Scope", text)
                    self.assertIn("**Done looks like:**", text)

    def test_markdown_child_links_work(self) -> None:
        path = self.story()
        path.write_text(
            path.read_text().replace(
                "`../tasks/TASK-docs.md`",
                "[documentation](../tasks/TASK-docs.md)",
            ),
            encoding="utf-8",
        )
        self.assert_result(path, "pass", "--gate", "route")

    def test_closed_card_cannot_claim_unfinished_children(self) -> None:
        path = self.story("closed", evidence())
        path.write_text(
            path.read_text().replace("- [x] TASK", "- [ ] TASK"),
            encoding="utf-8",
        )
        self.assert_result(path, "fail", "--gate", "review")

    def test_child_status_is_checked_independently_of_checkbox(self) -> None:
        path = self.story(proof=evidence())
        self.card("Task", "docs", "testing", evidence())
        self.assert_result(path, "blocked", "--gate", "review")

    def test_review_requirement_applies_only_to_selected_root(self) -> None:
        proof = evidence("E-review", kind="review")
        path = self.story(proof=proof)
        self.assert_result(
            path, "pass", "--gate", "review", "--require-review"
        )

    def test_require_review_also_checks_open_structural_card(self) -> None:
        self.assert_result(
            self.card(proof=evidence()), "blocked", "--require-review"
        )

    def test_metadata_duplicates_and_invalid_dates_fail(self) -> None:
        for replacement in [
            "**Owner:** contributor\n**Owner:** duplicate",
            "**Owner:** <contributor>",
        ]:
            path = self.card()
            path.write_text(
                path.read_text().replace(
                    "**Owner:** contributor", replacement
                ),
                encoding="utf-8",
            )
            with self.subTest(replacement=replacement):
                self.assert_result(path, "fail")
        path = self.card()
        path.write_text(
            path.read_text().replace("2026-11-15", "20261115"),
            encoding="utf-8",
        )
        self.assert_result(path, "fail")

    def test_all_hierarchy_levels_route_and_review(self) -> None:
        self.story("closed", evidence())
        self.card("SubTask", "leaf", "closed", evidence())
        self.card(
            "Task",
            "docs",
            "closed",
            evidence(),
            "## SubTask list\n- [x] [Leaf](../subtasks/SUBTASK-leaf.md)\n",
        )
        feature = self.card(
            "Feature",
            "feature",
            "closed",
            evidence(),
            "## Domain & Architecture (DDD)\n"
            "- **Bounded context:** Lifecycle validation.\n"
            "- **Subdomain classification:** Supporting\n"
            "- **Entities vs. Value Objects:** Cards have identity.\n"
            "- **Aggregate(s) and root(s):** One card owns its records.\n\n"
            "## Story list (FDD)\n"
            "- [x] [Story](../stories/STORY-story.md)\n",
        )
        epic = self.card(
            "Epic",
            "epic",
            "closed",
            evidence(),
            "## Features\n- [x] [Feature](../features/FEAT-feature.md)\n",
        )
        for path in (feature, epic):
            with self.subTest(kind=path.name):
                self.assert_result(path, "pass", "--gate", "route")
                self.assert_result(path, "pass", "--gate", "review")

    def test_feature_route_requires_the_existing_ddd_fields(self) -> None:
        self.story()
        path = self.card(
            "Feature",
            "feature",
            extra=(
                "## Domain & Architecture (DDD)\n"
                "- **Bounded context:** Lifecycle validation.\n"
                "- **Subdomain classification:** Supporting\n"
                "- **Entities vs. Value Objects:** Cards have identity.\n"
                "- **Aggregate(s) and root(s):** A card owns its records.\n\n"
                "## Story list (FDD)\n"
                "- [ ] [Story](../stories/STORY-story.md)\n"
            ),
        )
        self.assert_result(path, "pass", "--gate", "route")
        path.write_text(
            path.read_text().replace(
                "- **Bounded context:** Lifecycle validation.", ""
            ),
            encoding="utf-8",
        )
        self.assert_result(path, "fail", "--gate", "route")

    @unittest.skipIf(sys.version_info < (3, 11), "Codex generator needs 3.11")
    @unittest.skipIf(
        os.name == "nt",
        "install.sh is POSIX; on Windows `bash` resolves to WSL, not Git Bash",
    )
    def test_installers_copy_a_standalone_python_checker(self) -> None:
        path = self.card()
        install_root = Path(self.scratch.name) / "installed"
        claude_root = install_root / "claude"
        codex_root = install_root / "codex"
        env = dict(
            os.environ,
            PYTHONDONTWRITEBYTECODE="1",
            CLAUDE_HOME=str(claude_root),
            CODEX_HOME=str(codex_root),
        )
        install = subprocess.run(
            ["bash", str(REPOSITORY / "install.sh"), "--target", "all"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
            check=False,
        )
        self.assertEqual(
            install.returncode, 0, install.stderr or install.stdout
        )
        for target in (claude_root, codex_root):
            checker = target / "skills/zeno/scripts/check_lifecycle.py"
            with self.subTest(target=target.name):
                self.assertEqual(checker.read_bytes(), CHECKER.read_bytes())
                run = subprocess.run(
                    [sys.executable, str(checker), str(path), "--json"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(run.returncode, 0, run.stderr or run.stdout)
                self.assertEqual(json.loads(run.stdout)["result"], "pass")


class SafeCardReadTests(unittest.TestCase):
    """Exercise replacements at the exact moment a card is opened."""

    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve() / ".zeno"
        self.folder = self.root / "docs"
        self.folder.mkdir(parents=True)
        self.path = self.folder / "TASK-read.md"
        self.path.write_text(
            "# Task: read\n**Goal:** inside\n", encoding="utf-8"
        )
        spec = importlib.util.spec_from_file_location(
            "lifecycle_read_test", CHECKER
        )
        assert spec is not None and spec.loader is not None
        self.checker = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.checker
        self.addCleanup(sys.modules.pop, spec.name, None)
        spec.loader.exec_module(self.checker)

    @unittest.skipUnless(
        hasattr(os, "mkfifo") and os.open in os.supports_dir_fd,
        "Anchored FIFO open needs POSIX",
    )
    def test_fifo_replacement_is_rejected_after_path_resolution(self) -> None:
        original_open = os.open
        replaced = False

        def replace_before_open(
            path: Union[str, Path],  # noqa: UP007 - Python 3.8 target
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: Optional[int] = None,  # noqa: UP045 - Python 3.8 target
        ) -> int:
            nonlocal replaced
            if path == self.path.name and dir_fd is not None:
                self.path.unlink()
                os.mkfifo(self.path)
                replaced = True
            return original_open(path, flags, mode, dir_fd=dir_fd)

        validator = self.checker.Validator(self.root, None, False)
        with mock.patch.object(self.checker.os, "open", replace_before_open):
            card = validator.read(self.path)
        self.assertTrue(replaced)
        self.assertIsNone(card)
        self.assertTrue(validator.findings)

    @unittest.skipUnless(
        hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd,
        "Anchored directory traversal needs POSIX",
    )
    def test_parent_symlink_replacement_cannot_redirect_an_open(self) -> None:
        outside = Path(self.scratch.name).resolve() / "outside"
        outside.mkdir()
        (outside / self.path.name).write_text(
            "# Task: read\n**Goal:** outside\n", encoding="utf-8"
        )
        original_open = os.open
        replaced = False

        def replace_after_open(
            path: Union[str, Path],  # noqa: UP007 - Python 3.8 target
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: Optional[int] = None,  # noqa: UP045 - Python 3.8 target
        ) -> int:
            nonlocal replaced
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            if path == "docs" and dir_fd is not None:
                self.folder.rename(self.root / "pinned")
                self.folder.symlink_to(outside, target_is_directory=True)
                replaced = True
            return descriptor

        validator = self.checker.Validator(self.root, None, False)
        with mock.patch.object(self.checker.os, "open", replace_after_open):
            card = validator.read(self.path)
        self.assertTrue(replaced)
        self.assertIsNotNone(card)
        self.assertEqual(card.metadata["goal"], "inside")

    def test_portable_fallback_rejects_opened_identity_mismatch(self) -> None:
        outside = Path(self.scratch.name) / "different.md"
        outside.write_text("Different file identity", encoding="utf-8")
        original_open = os.open

        def open_different_file(
            path: Union[str, Path],  # noqa: UP007 - Python 3.8 target
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: Optional[int] = None,  # noqa: UP045 - Python 3.8 target
        ) -> int:
            if Path(path) == self.path:
                return original_open(outside, flags, mode, dir_fd=dir_fd)
            return original_open(path, flags, mode, dir_fd=dir_fd)

        validator = self.checker.Validator(self.root, None, False)
        with mock.patch.object(
            self.checker, "ANCHORED_READ", False
        ), mock.patch.object(self.checker.os, "open", open_different_file):
            card = validator.read(self.path)
        self.assertIsNone(card)
        self.assertTrue(validator.findings)

    def test_portable_fallback_reads_an_unchanged_regular_card(self) -> None:
        validator = self.checker.Validator(self.root, None, False)
        with mock.patch.object(self.checker, "ANCHORED_READ", False):
            card = validator.read(self.path)
        self.assertIsNotNone(card)
        self.assertEqual(card.metadata["goal"], "inside")


if __name__ == "__main__":
    unittest.main()
