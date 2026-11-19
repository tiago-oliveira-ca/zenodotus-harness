"""Guard the zeno-test-prune and zeno-untangle method leaves and their registration."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    """Return a file's text with whitespace collapsed, so wrapped phrases still match."""
    return " ".join((ROOT / relative).read_text(encoding="utf-8").split())


class TestPruneLeafTests(unittest.TestCase):
    """The test-prune leaf, its command and its registration."""

    LEAF = "skills/zeno-stack/zeno-test-prune/SKILL.md"

    def test_leaf_states_the_rule_and_the_rubric(self) -> None:
        leaf = read(self.LEAF)
        self.assertIn("KEEP A TEST ONLY IF IT CAN FAIL WHEN INTENDED BEHAVIOR BREAKS", leaf)
        for dependency in ("the past", "nothing", "the implementation", "a duplicate"):
            self.assertIn(dependency, leaf)
        self.assertIn("mutation check", leaf)
        self.assertIn("test-only production code", leaf)

    def test_leaf_has_both_enforcement_sections_last(self) -> None:
        text = (ROOT / self.LEAF).read_text(encoding="utf-8")
        self.assertIn("## Anti-pattern quick reference", text)
        last_heading = [line for line in text.splitlines() if line.startswith("## ")][-1]
        self.assertTrue(last_heading.startswith("## Pre-flight checklist — run before delivering any"))

    def test_dispatcher_command_and_codex_fold_register_it(self) -> None:
        self.assertIn("`zeno-test-prune/SKILL.md`", read("skills/zeno-stack/SKILL.md"))
        self.assertIn("prune tests", read("skills/zeno-stack/SKILL.md"))
        self.assertIn("zeno-test-prune", read("commands/prune-tests.md"))
        fold = read("tools/codex/fold-map.toml")
        self.assertIn('name = "prune-tests"', fold)
        self.assertIn('target = "skills/zeno-stack/zeno-test-prune/SKILL.md"', fold)

    def test_testing_leaves_point_back(self) -> None:
        for leaf in ("zeno-python-testing", "zeno-react-testing", "zeno-e2e-testing"):
            with self.subTest(leaf=leaf):
                self.assertIn("zeno-test-prune", read(f"skills/zeno-stack/{leaf}/SKILL.md"))


class UntangleLeafTests(unittest.TestCase):
    """The untangle leaf, its user-only command and its registration."""

    LEAF = "skills/zeno-stack/zeno-untangle/SKILL.md"

    def test_leaf_states_the_rule_phases_and_taxonomy(self) -> None:
        leaf = read(self.LEAF)
        self.assertIn("NO CHANGE BEFORE THE INVENTORY IS ON A CARD", leaf)
        for kind in ("Hidden link", "Needless link", "Surplus", "Special case"):
            self.assertIn(kind, leaf)
        self.assertIn("cluster", leaf)
        self.assertIn("one Story per cluster", leaf)
        self.assertIn("Stop rubric", leaf)
        self.assertIn("pin current behavior", leaf)

    def test_leaf_has_both_enforcement_sections_last(self) -> None:
        text = (ROOT / self.LEAF).read_text(encoding="utf-8")
        self.assertIn("## Anti-pattern quick reference", text)
        last_heading = [line for line in text.splitlines() if line.startswith("## ")][-1]
        self.assertTrue(last_heading.startswith("## Pre-flight checklist — run before delivering any"))

    def test_command_is_user_only_and_folded(self) -> None:
        command = (ROOT / "commands/untangle.md").read_text(encoding="utf-8")
        front = command.split("---")[1]
        self.assertIn("disable-model-invocation: true", front)
        self.assertIn("zeno-untangle", command)
        fold = read("tools/codex/fold-map.toml")
        self.assertIn('name = "untangle"', fold)
        self.assertIn('target = "skills/zeno-stack/zeno-untangle/SKILL.md"', fold)

    def test_dispatcher_and_cleanup_point_both_ways(self) -> None:
        dispatcher = read("skills/zeno-stack/SKILL.md")
        self.assertIn("`zeno-untangle/SKILL.md`", dispatcher)
        self.assertIn("/untangle", dispatcher)
        self.assertIn("zeno-untangle", read("skills/zeno-stack/zeno-refactor-cleanup/SKILL.md"))
        self.assertIn("zeno-refactor-cleanup", read(self.LEAF))
        self.assertIn("zeno-test-prune", read(self.LEAF))


class LoopIntegrationTests(unittest.TestCase):
    """The two leaves fit the zeno gates without contradicting them, and the loop points to them."""

    UNTANGLE = "skills/zeno-stack/zeno-untangle/SKILL.md"
    TDD = "skills/zeno-workflow/zeno-tdd/SKILL.md"

    def test_tdd_defines_red_for_behavior_preserving_tasks(self) -> None:
        tdd = read(self.TDD)
        self.assertIn("Behavior-preserving Tasks", tdd)
        self.assertIn("deliberate break", tdd)
        self.assertIn("zeno-untangle", tdd)

    def test_tdd_scopes_its_no_delete_rule_to_pruning(self) -> None:
        tdd = read(self.TDD)
        self.assertIn("zeno-test-prune", tdd)
        self.assertIn("recorded mutation check", tdd)

    def test_feature_template_has_an_optional_findings_section(self) -> None:
        template = (ROOT / "skills/zeno/references/feature-template.md").read_text(encoding="utf-8")
        self.assertIn("## Findings", template)
        self.assertIn("## Findings", read(self.UNTANGLE))

    def test_untangle_states_how_it_fits_each_gate(self) -> None:
        leaf = read(self.UNTANGLE)
        for phrase in ("reopens Gate 2", "follow-up Feature", "Full council", "Epic",
                       "BREAKING API CHANGE", "zeno-ddd", "WIP limit 1", "Behavior-preserving Tasks"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, leaf)

    def test_commands_open_the_zeno_loop_first(self) -> None:
        for command in ("commands/untangle.md", "commands/prune-tests.md"):
            with self.subTest(command=command):
                self.assertIn("Open the zeno loop", read(command))

    def test_loop_suggests_the_leaves(self) -> None:
        for path in ("skills/zeno-debug/SKILL.md", "skills/zeno-verify/SKILL.md"):
            with self.subTest(path=path):
                self.assertIn("suggest `/untangle`", read(path))
        for path in ("agents/zeno-pr-test-analyzer.md", "commands/test-coverage.md"):
            with self.subTest(path=path):
                self.assertIn("/prune-tests", read(path))


if __name__ == "__main__":
    unittest.main()
