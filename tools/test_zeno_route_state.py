"""Guard Zeno Gate 2's route-state rules: dirty-path classification, migration order,
re-read before write, and content-based methodology currency."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RouteStateTests(unittest.TestCase):
    """Check Gate 2 in the zeno skill."""

    def setUp(self) -> None:
        text = (ROOT / "skills/zeno/SKILL.md").read_text(encoding="utf-8")
        start = text.index("## Gate 2")
        end = text.index("## Gate 3")
        self.gate2 = " ".join(text[start:end].split())
        self.whole = " ".join(text.split())

    def test_every_dirty_path_is_classified(self) -> None:
        self.assertIn("classify every dirty path", self.gate2)
        self.assertIn("unknown", self.gate2)
        self.assertIn("clean worktree", self.gate2)

    def test_migration_runs_before_state_is_created(self) -> None:
        migrate = self.gate2.index("Migrate a legacy thread")
        create = self.gate2.index("Ensure a repo-root `./.zeno/` folder exists")
        self.assertLess(migrate, create)

    def test_each_write_is_preceded_by_a_re_read(self) -> None:
        self.assertIn("Immediately before every `project.md` or card write", self.gate2)

    def test_currency_is_proved_by_content_not_mtime(self) -> None:
        self.assertIn("build_codex.py --out", self.gate2)
        self.assertIn("never proof of currency", self.gate2)
        self.assertNotIn("its file mtime is enough", self.whole)


if __name__ == "__main__":
    unittest.main()
