#!/usr/bin/env python3
"""Check explicitly selected Zeno cards without executing their evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple, TypedDict

SCOPE = (
    "card integrity only. Factual truth, actual execution, freshness, "
    "reviewer independence, safety and human approval remain unverified"
)
CARD_TYPES = {
    "EPIC": "Epic",
    "FEAT": "Feature",
    "STORY": "Story",
    "TASK": "Task",
    "SUBTASK": "SubTask",
}
CHILDREN = {
    "Epic": ("Features", "Feature"),
    "Feature": ("Story list", "Story"),
    "Story": ("Task list", "Task"),
    "Task": ("SubTask list", "SubTask"),
}
REQUIRED_PROOF_FIELDS = (
    "claim",
    "required",
    "kind",
    "result",
    "evidence",
    "revision",
    "environment",
    "owner",
)
RESULTS = {"pass", "fail", "blocked", "not_run", "not_applicable"}
BOLD_FIELD = re.compile(r"^\s*(?:-\s+)?\*\*([^*]+):\*\*\s*(.*?)\s*$")
PROOF_FIELD = re.compile(r"^\s*-\s+([A-Za-z][A-Za-z ]*):\s*(.*?)\s*$")
CHECKBOX = re.compile(r"^\s*[-*]\s+\[([^\]]*)\]\s+(.*)$")
EVIDENCE_ID = re.compile(r"E-[A-Za-z0-9][A-Za-z0-9_-]*\Z")
ANCHORED_READ = (
    os.open in os.supports_dir_fd
    and hasattr(os, "O_NOFOLLOW")
    and hasattr(os, "O_DIRECTORY")
    and hasattr(os, "O_NONBLOCK")
)
PATH_SAFETY = (
    "POSIX descriptor-anchored reads with non-following, nonblocking "
    "regular-file opens."
    if ANCHORED_READ
    else "Portable pre-read identity checks. Concurrent path replacement "
    "remains unsupported and lacks atomic protection on this platform."
)


class Finding(TypedDict):
    """An integrity issue associated with the card that declares it."""

    path: str
    result: str
    message: str


class Report(TypedDict):
    """The stable JSON-compatible result of a selected hierarchy check."""

    result: str
    scope: str
    path_safety: str
    card: str
    gate: str
    checked_cards: List[str]
    findings: List[Finding]


@dataclass
class Card:
    """The visible metadata and sections from a single selected file."""

    path: Path
    kind: Optional[str]
    metadata: Dict[str, str]
    sections: Dict[str, str]

    @property
    def closed(self) -> bool:
        """Whether this card claims closure."""
        return self.metadata.get("status") == "closed"

    def section(self, name: str) -> Optional[str]:
        """Get a section by its canonical name."""
        return self.sections.get(name.lower())


def visible_markdown(text: str) -> str:
    """Keep top-level records outside comments and code examples."""
    lines = []
    fence = ""
    fence_length = 0
    comment = False
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (
                marker
                and marker.group(1)[0] == fence
                and len(marker.group(1)) >= fence_length
                and not marker.group(2).strip()
            ):
                fence = ""
            continue
        if not comment and (line.startswith("    ") or line.startswith("\t")):
            continue
        visible = []
        while line:
            if comment:
                end = line.find("-->")
                if end < 0:
                    break
                line = line[end + 3 :]
                comment = False
            else:
                start = line.find("<!--")
                if start < 0:
                    visible.append(line)
                    break
                visible.append(line[:start])
                line = line[start + 4 :]
                comment = True
        line = "".join(visible)
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            fence = marker.group(1)[0]
            fence_length = len(marker.group(1))
            continue
        if not (line.startswith("    ") or line.startswith("\t")):
            lines.append(line)
    return "\n".join(lines)


def meaningful(value: str) -> bool:
    """Reject empty values and recognizable unfilled template placeholders."""
    value = re.sub(r"<[^>]*>", "", value, flags=re.DOTALL)
    lines = []
    for line in value.splitlines():
        line = re.sub(r"^\s*(?:[-*+]\s+)?\[[ xX~]\](?:\s+|$)", "", line)
        lines.append(line.strip(" \t\r\n`*_#>~-"))
    value = " ".join(lines).strip()
    if not value or not re.search(r"\w", value):
        return False
    return not re.match(
        r"^(?:todo|tbd|pending|placeholder|n/a|none)\b", value, re.I
    )


def fields(text: str) -> Tuple[Dict[str, str], List[str]]:
    """Read scalar fields and retain their duplicate names."""
    values = {}
    duplicates = []
    for line in text.splitlines():
        match = BOLD_FIELD.match(line) or PROOF_FIELD.match(line)
        if not match:
            continue
        key, value = match.group(1).lower(), match.group(2)
        if key in values:
            duplicates.append(key)
        values[key] = value
    return values, duplicates


def read_card_text(path: Path, root: Path) -> str:
    """Read a regular card with anchored or identity-checked file access."""
    path.relative_to(root)
    flags = (
        os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    )
    snapshots: List[Tuple[Path, os.stat_result]] = []
    if ANCHORED_READ:
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory = os.open(path.anchor, directory_flags)
        try:
            for component in path.parts[1:-1]:
                opened = os.open(component, directory_flags, dir_fd=directory)
                os.close(directory)
                directory = opened
            descriptor = os.open(
                path.name, flags | os.O_NOFOLLOW, dir_fd=directory
            )
        finally:
            os.close(directory)
    else:
        snapshots = [(part, os.lstat(part)) for part in (*path.parents, path)]
        if any(stat.S_ISLNK(info.st_mode) for _, info in snapshots):
            raise ValueError("Card path changed to a symbolic link.")
        if not stat.S_ISREG(snapshots[-1][1].st_mode):
            raise ValueError("Card must be a regular file.")
        descriptor = os.open(path, flags)
    try:
        opened_info = os.fstat(descriptor)
        if not stat.S_ISREG(opened_info.st_mode):
            raise ValueError("Card must be a regular file.")
        if snapshots:
            if not os.path.samestat(snapshots[-1][1], opened_info):
                raise ValueError("Opened card identity changed.")
            if any(
                not os.path.samestat(before, os.lstat(part))
                for part, before in snapshots
            ):
                raise ValueError("Card path identity changed before reading.")
        with os.fdopen(
            descriptor, "r", encoding="utf-8", closefd=False
        ) as stream:
            return stream.read()
    finally:
        os.close(descriptor)


class Validator:
    """Validate one explicit hierarchy, keeping every read inside its root."""

    def __init__(
        self, root: Path, gate: Optional[str], require_review: bool
    ) -> None:
        """Configure the read boundary and selected metadata checks."""
        self.root = root
        self.gate = gate
        self.require_review = require_review
        self.findings: List[Finding] = []
        self.cards: Dict[Path, Card] = {}
        self.active: Set[Path] = set()

    def issue(self, path: Path, result: str, message: str) -> None:
        """Preserve failures and blocked requirements in discovery order."""
        self.findings.append(
            {"path": str(path), "result": result, "message": message}
        )

    def resolve(self, path: Path, declared_by: Path) -> Optional[Path]:
        """Resolve symlinks and refuse paths outside the selected root."""
        try:
            resolved = path.resolve()
            resolved.relative_to(self.root)
        except (OSError, RuntimeError, ValueError):
            self.issue(
                declared_by,
                "fail",
                "Card path escapes root or cannot resolve.",
            )
            return None
        return resolved

    def read(self, path: Path) -> Optional[Card]:
        """Read one card, surfacing filesystem and decoding failures."""
        try:
            text = visible_markdown(read_card_text(path, self.root))
        except UnicodeError as error:
            self.issue(path, "fail", "Card is not valid UTF-8: " + str(error))
            return None
        except ValueError as error:
            self.issue(path, "fail", str(error))
            return None
        except OSError as error:
            self.issue(path, "blocked", "Card is unavailable: " + str(error))
            return None

        filename = re.fullmatch(
            r"(EPIC|FEAT|STORY|TASK|SUBTASK)-(.+)\.md", path.name
        )
        kind = CARD_TYPES[filename.group(1)] if filename else None
        if kind is None:
            self.issue(
                path, "fail", "Filename must identify a supported card type."
            )
        titles = re.findall(r"^# ([^\n]+)$", text, flags=re.MULTILINE)
        if len(titles) != 1 or not re.fullmatch(
            re.escape(kind or "") + r":\s*\S.*", titles[0] if titles else ""
        ):
            self.issue(
                path, "fail", "Card header must match its filename type."
            )

        chunks = re.split(r"^## ([^\n]+)\s*$", text, flags=re.MULTILINE)
        metadata, duplicates = fields(chunks[0])
        for field in duplicates:
            self.issue(path, "fail", "Duplicate metadata field: " + field)
        sections = {}
        for index in range(1, len(chunks), 2):
            name = re.sub(
                r"(?:\s+\([^)]*\))+$", "", chunks[index].strip().lower()
            )
            if name in sections:
                self.issue(path, "fail", "Duplicate section: " + name)
            sections[name] = chunks[index + 1]
        return Card(path, kind, metadata, sections)

    def structure(self, card: Card) -> None:
        """Check the common card shape and scoped-card declarations."""
        for name in ("goal", "status", "owner", "updated"):
            if not meaningful(card.metadata.get(name, "")):
                self.issue(
                    card.path,
                    "fail",
                    "Missing or placeholder metadata: " + name,
                )
        if card.metadata.get("status") not in {
            "backlog",
            "development",
            "testing",
            "closed",
        }:
            self.issue(
                card.path,
                "fail",
                "Status must be backlog, development, testing or closed.",
            )
        try:
            updated = card.metadata.get("updated", "")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", updated):
                raise ValueError("Expected YYYY-MM-DD")
            date.fromisoformat(updated)
        except ValueError:
            self.issue(
                card.path, "fail", "Updated must be a valid YYYY-MM-DD date."
            )
        for name in ("Decisions", "Proof", "Outcome"):
            if card.section(name) is None:
                self.issue(card.path, "fail", "Missing section: " + name)
        if card.closed and not meaningful(card.section("Outcome") or ""):
            self.issue(
                card.path,
                "fail",
                "Closed card needs a non-placeholder Outcome.",
            )
        if card.kind in {"Epic", "Feature", "Story"}:
            scope, duplicates = fields(card.section("Scope") or "")
            for name in duplicates:
                self.issue(card.path, "fail", "Duplicate Scope field: " + name)
            for name in ("problem", "approach", "done looks like"):
                if not meaningful(scope.get(name, "")):
                    self.issue(
                        card.path,
                        "fail",
                        "Missing or placeholder Scope field: " + name,
                    )

    def planning(self, card: Card) -> None:
        """Check the route-specific planning sections for each card tier."""
        if card.kind in {"Task", "SubTask"} and not meaningful(
            card.section("Description") or ""
        ):
            self.issue(
                card.path, "fail", "Route needs a concrete Description."
            )
        if card.kind == "Feature":
            domain, duplicates = fields(
                card.section("Domain & Architecture") or ""
            )
            for name in duplicates:
                self.issue(card.path, "fail", "Duplicate DDD field: " + name)
            for name in (
                "bounded context",
                "subdomain classification",
                "entities vs. value objects",
                "aggregate(s) and root(s)",
            ):
                if not meaningful(domain.get(name, "")):
                    self.issue(
                        card.path,
                        "fail",
                        "Missing or placeholder DDD field: " + name,
                    )
        if card.kind != "Story":
            return
        if not meaningful(card.section("Acceptance criteria") or ""):
            self.issue(
                card.path, "fail", "Story route needs Acceptance criteria."
            )
        scenarios = card.section("Scenarios") or ""
        examples = re.split(
            r"^### Scenario:\s*.+$", scenarios, flags=re.MULTILINE
        )[1:]
        if not examples:
            self.issue(
                card.path,
                "fail",
                "Story route needs Given/When/Then scenarios.",
            )
        for example in examples:
            for keyword in ("Given", "When", "Then"):
                match = re.search(
                    r"^\s*(?:-\s*)?(?:\*\*)?" + keyword + r"(?:\*\*)?\s+(.+)$",
                    example,
                    flags=re.MULTILINE,
                )
                if not match or not meaningful(match.group(1)):
                    self.issue(
                        card.path,
                        "fail",
                        "Scenario needs a concrete " + keyword + " step.",
                    )

    def proof(self, card: Card, require_review: bool) -> None:
        """Validate evidence fields, supersession and required states."""
        records: Dict[str, Dict[str, str]] = {}
        chunks = re.split(
            r"^### ([^\n]+)\s*$",
            card.section("Proof") or "",
            flags=re.MULTILINE,
        )
        for index in range(1, len(chunks), 2):
            identifier = chunks[index].strip()
            if not EVIDENCE_ID.fullmatch(identifier):
                self.issue(
                    card.path, "fail", "Invalid evidence ID: " + identifier
                )
                continue
            if identifier in records:
                self.issue(
                    card.path, "fail", "Duplicate evidence ID: " + identifier
                )
            record, duplicates = fields(chunks[index + 1])
            records[identifier] = record
            for name in duplicates:
                self.issue(
                    card.path,
                    "fail",
                    identifier + " has duplicate field: " + name,
                )
            for name in REQUIRED_PROOF_FIELDS:
                if not meaningful(record.get(name, "")):
                    self.issue(
                        card.path, "fail", identifier + " needs field: " + name
                    )
            for name, choices in (
                ("required", {"yes", "no"}),
                ("kind", {"check", "review"}),
                ("result", RESULTS),
            ):
                if record.get(name) not in choices:
                    self.issue(
                        card.path,
                        "fail",
                        identifier + " has invalid " + name + ".",
                    )
            if record.get("result") == "not_applicable" and not meaningful(
                record.get("reason", "")
            ):
                self.issue(
                    card.path,
                    "fail",
                    identifier + " needs a not_applicable Reason.",
                )

        superseded = set()
        for identifier, record in records.items():
            previous = record.get("supersedes")
            if previous is None:
                continue
            if previous not in records:
                self.issue(
                    card.path,
                    "fail",
                    identifier + " supersedes a missing evidence ID.",
                )
                continue
            for field in ("claim", "required", "kind"):
                if record.get(field) != records[previous].get(field):
                    self.issue(
                        card.path,
                        "fail",
                        identifier + " supersedes a different " + field + ".",
                    )
            superseded.add(previous)
            seen = {identifier}
            cursor = previous
            while cursor in records:
                if cursor in seen:
                    self.issue(
                        card.path,
                        "fail",
                        "Evidence supersession contains a cycle.",
                    )
                    break
                seen.add(cursor)
                cursor = records[cursor].get("supersedes", "")

        if not (self.gate == "review" or card.closed or require_review):
            return
        current = [
            record
            for identifier, record in records.items()
            if identifier not in superseded
        ]
        required = [
            record for record in current if record.get("required") == "yes"
        ]
        if not required:
            self.issue(
                card.path,
                "blocked",
                "Review needs current required Proof records.",
            )
        for record in required:
            result = record.get("result")
            if result == "fail":
                self.issue(
                    card.path,
                    "fail",
                    "Required evidence failed: " + record.get("claim", ""),
                )
            elif result in {"blocked", "not_run"}:
                self.issue(
                    card.path,
                    "blocked",
                    "Required evidence is "
                    + result
                    + ": "
                    + record.get("claim", ""),
                )
        if require_review and not any(
            record.get("kind") == "review" and record.get("result") == "pass"
            for record in required
        ):
            self.issue(
                card.path,
                "blocked",
                "Independent review needs a current required "
                "passing review record.",
            )

    def children(self, card: Card) -> List[Tuple[str, Path, str]]:
        """Resolve targets in this card's hierarchy checklist."""
        hierarchy = CHILDREN.get(card.kind or "")
        if hierarchy is None:
            return []
        section_name, child_kind = hierarchy
        section = card.section(section_name)
        entries = []
        for line in (section or "").splitlines():
            match = CHECKBOX.match(line)
            if match:
                entries.append((match.group(1), match.group(2)))
        if self.gate in {"route", "review"}:
            if not entries and (card.kind != "Task" or section is not None):
                self.issue(
                    card.path,
                    "fail",
                    "Route needs linked checkbox entries in "
                    + section_name
                    + ".",
                )
            if (
                card.kind == "Story"
                and entries
                and "[documentation]" not in entries[-1][1]
            ):
                self.issue(
                    card.path,
                    "fail",
                    "Last Task needs the [documentation] marker.",
                )
        children = []
        for marker, body in entries:
            if marker not in {" ", "~", "x", "X"}:
                self.issue(card.path, "fail", "Invalid child checkbox state.")
            paths = re.findall(r"`([^`\n]+\.md)`", body)
            paths.extend(re.findall(r"\[[^\]\n]*\]\(([^)\n]+\.md)\)", body))
            if len(paths) != 1:
                self.issue(
                    card.path,
                    "fail",
                    "Each child checkbox needs exactly one relative "
                    "Markdown target.",
                )
                continue
            target = paths[0]
            if Path(target).is_absolute() or ":" in target or "\\" in target:
                self.issue(
                    card.path,
                    "fail",
                    "Child target must be a relative Markdown path.",
                )
                continue
            resolved = self.resolve(card.path.parent / target, card.path)
            if resolved is not None:
                children.append((marker, resolved, child_kind))
        return children

    def visit(
        self,
        path: Path,
        expected_kind: Optional[str] = None,
        is_root: bool = False,
    ) -> Optional[Card]:
        """Walk explicit children once and reject active-path cycles."""
        if path in self.active:
            self.issue(path, "fail", "Child links contain a cycle.")
            return None
        card = self.cards.get(path)
        if (
            card is not None
            and expected_kind is not None
            and card.kind != expected_kind
        ):
            self.issue(
                path, "fail", "Parent requires a " + expected_kind + " child."
            )
            return card
        if card is None:
            card = self.read(path)
            if card is None:
                return None
            self.cards[path] = card
            if expected_kind is not None and card.kind != expected_kind:
                self.issue(
                    path,
                    "fail",
                    "Parent requires a " + expected_kind + " child.",
                )
                return card
            self.active.add(path)
            self.structure(card)
            if self.gate in {"route", "review"}:
                self.planning(card)
            self.proof(card, is_root and self.require_review)
            for marker, child_path, child_kind in self.children(card):
                child = self.visit(child_path, child_kind)
                if self.gate == "review" or card.closed:
                    result = "fail" if card.closed else "blocked"
                    if marker.lower() != "x":
                        self.issue(
                            card.path,
                            result,
                            "Child checkbox is unfinished: " + str(child_path),
                        )
                    if child is not None and not child.closed:
                        self.issue(
                            card.path,
                            result,
                            "Child card is not closed: " + str(child_path),
                        )
            self.active.remove(path)
        return card


def check_card(
    path: Path,
    root: Optional[Path] = None,
    gate: Optional[str] = None,
    require_review: bool = False,
) -> Report:
    """Return a read-only integrity report for a card and explicit children."""
    path = Path(path).absolute()
    if root is None:
        root = next(
            (parent for parent in path.parents if parent.name == ".zeno"), None
        )
    if root is None:
        return {
            "result": "fail",
            "scope": SCOPE,
            "path_safety": PATH_SAFETY,
            "card": str(path),
            "gate": gate or "structural",
            "checked_cards": [],
            "findings": [
                {
                    "path": str(path),
                    "result": "fail",
                    "message": "No .zeno ancestor; supply --root.",
                }
            ],
        }
    try:
        root = Path(root).resolve()
    except (OSError, RuntimeError) as error:
        return {
            "result": "fail",
            "scope": SCOPE,
            "path_safety": PATH_SAFETY,
            "card": str(path),
            "gate": gate or "structural",
            "checked_cards": [],
            "findings": [
                {
                    "path": str(path),
                    "result": "fail",
                    "message": "Root cannot resolve: " + str(error),
                }
            ],
        }
    validator = Validator(root, gate, require_review)
    selected = validator.resolve(path, path)
    if selected is not None:
        validator.visit(selected, is_root=True)
    results = {finding["result"] for finding in validator.findings}
    result = (
        "fail"
        if "fail" in results
        else "blocked"
        if "blocked" in results
        else "pass"
    )
    return {
        "result": result,
        "scope": SCOPE,
        "path_safety": PATH_SAFETY,
        "card": str(path),
        "gate": gate or "structural",
        "checked_cards": [str(card) for card in validator.cards],
        "findings": validator.findings,
    }


def main(arguments: Optional[Sequence[str]] = None) -> int:
    """Print an integrity report and return pass/fail/blocked as 0/1/2."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path, help="explicit card to check")
    parser.add_argument(
        "--root",
        type=Path,
        help="allowed card root (default nearest .zeno ancestor)",
    )
    parser.add_argument(
        "--gate",
        choices=("route", "review"),
        help="additional gate checks (default structural)",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit a JSON report"
    )
    parser.add_argument(
        "--require-review",
        action="store_true",
        help="require passing review metadata on the selected card",
    )
    options = parser.parse_args(arguments)
    report = check_card(
        options.card, options.root, options.gate, options.require_review
    )
    if options.json:
        print(json.dumps(report, indent=2))
    else:
        print(str(report["result"]).upper() + " — " + str(report["card"]))
        print(report["scope"])
        print(report["path_safety"])
        for finding in report["findings"]:
            print(
                f"{finding['result']}: {finding['path']} "
                f"— {finding['message']}"
            )
    return {"pass": 0, "fail": 1, "blocked": 2}[report["result"]]


if __name__ == "__main__":
    raise SystemExit(main())
