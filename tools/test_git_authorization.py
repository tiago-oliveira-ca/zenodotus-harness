"""Guard Zeno's explicit authorization boundary for git mutations."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GitAuthorizationTests(unittest.TestCase):
    """Check the owning workflow and its known mutation entry points."""

    def read(self, relative: str) -> str:
        content = (ROOT / relative).read_text(encoding="utf-8")
        return " ".join(content.split())

    def test_git_owner_defines_scoped_authorization(self) -> None:
        content = self.read("skills/zeno-stack/zeno-git-workflow/SKILL.md")
        self.assertIn("## Authorization", content)
        for operation in ("commit", "push", "PR", "merge"):
            self.assertIn(operation, content)
        self.assertIn("explicit project instructions", content)
        self.assertIn("working-tree", content)

    def test_execution_and_review_preserve_uncommitted_handoff(self) -> None:
        for relative in (
            "skills/zeno/SKILL.md",
            "skills/zeno-verify/SKILL.md",
            "skills/zeno-workflow/zeno-tdd/SKILL.md",
        ):
            with self.subTest(path=relative):
                content = self.read(relative)
                self.assertIn("authorization", content)
                self.assertIn("working-tree", content)
                for obsolete in (
                    "Committing to the working branch is your own duty",
                    "never needed permission",
                    "you never need permission",
                    "commit first (Gate 3's duty",
                    "only integration is gated",
                    "Commit any outstanding work first",
                ):
                    self.assertNotIn(obsolete, content)

    def test_mutation_entry_points_reference_authorization(self) -> None:
        for relative in (
            "commands/pr.md",
            "commands/checkpoint.md",
            "skills/zeno-stack/zeno-github-ops/SKILL.md",
            "skills/zeno-stack/zeno-refactor-cleanup/SKILL.md",
            "agents/zeno-refactor-cleaner.md",
        ):
            with self.subTest(path=relative):
                self.assertIn("authorization", self.read(relative))


if __name__ == "__main__":
    unittest.main()
