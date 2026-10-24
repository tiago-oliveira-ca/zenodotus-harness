#!/usr/bin/env python3
"""Generate a Codex-CLI-targeted skills tree from Zenodotus's single source.

Reads tools/codex/fold-map.toml and:
  1. Mirrors skills/ into <out>/skills/, applying Class A path/terminology substitution
     (~/.claude -> ~/.codex, .claude/ -> .codex/, "Claude Code" -> "Codex") to every text file,
     and skipping anything matched by an `excluded` glob (e.g. evals/evals.json fixtures).
  2. Folds each agents/*.md and commands/*.md file (per the manifest) into its target skill as a
     new, clearly-titled section, appended after the target's existing content — never mirrored
     as a standalone file, since Codex has no per-file tool-scoped subagent primitive.

Zero external dependencies (stdlib only, including `tomllib`, Python 3.11+), matching the
install-tooling ethos already established by install.sh. Never writes into a real $CODEX_HOME
directly -- always writes to --out; install-codex.sh is what copies the result into place.
"""

import argparse
import fnmatch
import os
import pathlib
import shutil
import sys
from typing import TypedDict

import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[2]
FOLD_MAP_PATH = ROOT / "tools" / "codex" / "fold-map.toml"
GENERATED_MARKER = ".zenodotus-codex-generated"


class GenerationReport(TypedDict):
    """Results accumulated while folding source content."""

    folded: list[str]
    relocated: list[str]
    missing_targets: list[str]
    errors: list[str]


CLASS_A_SUBSTITUTIONS = [
    ("~/.claude", "~/.codex"),
    (".claude/", ".codex/"),
    ("Claude Code", "Codex"),
]


def paths_overlap(first: pathlib.Path, second: pathlib.Path) -> bool:
    """Return whether either resolved path contains the other."""
    return first == second or first in second.parents or second in first.parents


def validate_output_path(candidate: str | os.PathLike[str]) -> pathlib.Path:
    """Resolve an output path and reject locations generation could damage."""
    output_path = pathlib.Path(candidate).resolve()
    protected_paths = [ROOT]

    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        protected_paths.append(pathlib.Path(codex_home).resolve())
    else:
        protected_paths.append(pathlib.Path.home() / ".codex")

    for protected_path in protected_paths:
        if paths_overlap(output_path, protected_path):
            raise ValueError(
                f"refusing unsafe output path {output_path}: overlaps "
                f"protected path {protected_path}"
            )

    return output_path


def prepare_output_directory(candidate: str | os.PathLike[str]) -> pathlib.Path:
    """Create a fresh output directory or replace verified generated output."""
    output_path = validate_output_path(candidate)
    marker_path = output_path / GENERATED_MARKER

    if output_path.exists():
        expected_marker = f"{ROOT}\n"
        try:
            marker_matches = marker_path.read_text() == expected_marker
        except (OSError, UnicodeError):
            marker_matches = False
        if not output_path.is_dir() or not marker_matches:
            raise ValueError(
                f"refusing to overwrite unowned output path {output_path}; "
                "choose a new path"
            )
        shutil.rmtree(output_path)

    output_path.mkdir(parents=True)
    marker_path.write_text(f"{ROOT}\n")
    return output_path


def report_has_failures(report: GenerationReport) -> bool:
    """Return whether generation omitted any required source or target."""
    return bool(report["missing_targets"] or report["errors"])


def load_fold_map():
    with open(FOLD_MAP_PATH, "rb") as f:
        return tomllib.load(f)


def apply_class_a(text):
    for old, new in CLASS_A_SUBSTITUTIONS:
        text = text.replace(old, new)
    return text


def excluded_globs(fold_map):
    return [e["glob"] for e in fold_map["excluded"] if "glob" in e]


def copy_skills_tree(src_skills, out_root, globs):
    for src_file in sorted(src_skills.rglob("*")):
        if src_file.is_dir():
            continue
        rel = src_file.relative_to(ROOT)  # e.g. skills/foo/SKILL.md
        rel_str = str(rel)
        if any(fnmatch.fnmatch(rel_str, g) for g in globs):
            continue
        dest = out_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = src_file.read_text()
        except UnicodeDecodeError:
            shutil.copy2(
                src_file, dest
            )  # binary asset (e.g. an .svg diagram) -- copy verbatim
            continue
        dest.write_text(apply_class_a(text))


def strip_frontmatter(text):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :].lstrip("\n")
    return text


def role_prefix(tier):
    if tier == "Advisor":
        return "_Role: Advisor — read-only guidance; does not itself edit code._\n\n"
    return "_Role: Owner — may edit within the Constraints stated below._\n\n"


def fold_one(
    src_path, target_rel, out_root, section_title, prefix, report, source_label
):
    if not src_path.exists():
        report["errors"].append(f"source missing: {src_path}")
        return
    target = out_root / target_rel
    if not target.exists():
        report["missing_targets"].append(target_rel)
        return
    body = apply_class_a(strip_frontmatter(src_path.read_text())).strip()
    section = f"\n\n## {section_title}\n\n{prefix}{body}\n"
    with open(target, "a") as f:
        f.write(section)
    report["folded"].append(source_label)


def fold_agents(fold_map, out_root, report):
    for entry in fold_map["agents"]:
        fold_one(
            ROOT / "agents" / f"{entry['name']}.md",
            entry["target"],
            out_root,
            entry["section_title"],
            role_prefix(entry["tier"]),
            report,
            f"agents/{entry['name']}.md",
        )


def fold_commands(fold_map, out_root, report):
    for entry in fold_map["commands"]:
        if entry["kind"] != "fold":
            report["relocated"].append(f"commands/{entry['name']}.md")
            continue
        fold_one(
            ROOT / "commands" / f"{entry['name']}.md",
            entry["target"],
            out_root,
            entry["section_title"],
            "",
            report,
            f"commands/{entry['name']}.md",
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        required=True,
        help="new output directory, or prior output carrying the generator marker",
    )
    args = parser.parse_args()

    fold_map = load_fold_map()
    try:
        out_root = prepare_output_directory(args.out)
    except ValueError as error:
        parser.error(str(error))

    globs = excluded_globs(fold_map)
    copy_skills_tree(ROOT / "skills", out_root, globs)

    report: GenerationReport = {
        "folded": [],
        "relocated": [],
        "missing_targets": [],
        "errors": [],
    }
    fold_agents(fold_map, out_root, report)
    fold_commands(fold_map, out_root, report)

    n_md = sum(1 for _ in out_root.rglob("*.md"))
    print(f"output: {out_root}")
    print(f"skills files written: {n_md}")
    print(f"folded: {len(report['folded'])}")
    print(
        f"relocated (rewritten by hand into source, not generated): {len(report['relocated'])}"
    )
    if report["missing_targets"]:
        print(
            f"! missing fold targets ({len(set(report['missing_targets']))}) -- create these skills first:"
        )
        for t in sorted(set(report["missing_targets"])):
            print(f"  - {t}")
    if report["errors"]:
        print("! errors:")
        for e in report["errors"]:
            print(f"  - {e}")
    if report_has_failures(report):
        sys.exit(1)


if __name__ == "__main__":
    main()
