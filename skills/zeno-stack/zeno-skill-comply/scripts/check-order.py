#!/usr/bin/env python3
"""check-order.py — verify step ordering in a captured tool-call timeline.

Usage:
  extract-trace.py PROJECT_DIR --json | check-order.py "BEFORE:AFTER" ["BEFORE:AFTER" ...]
  check-order.py --trace trace.json "Skill=zeno:Edit" "Bash~branch --show-current:Edit"

Rule syntax — "BEFORE:AFTER", where each side is a matcher:
  Edit                      tool name is Edit
  Skill=zeno                tool name is Skill AND its detail/input contains "zeno"
  Bash~git commit           tool name is Bash AND its command contains "git commit"
                            (= and ~ are equivalent; both are substring, case-insensitive)

A rule PASSES when the first BEFORE match occurs earlier than the first AFTER match.
It FAILS when BEFORE is missing, or occurs after AFTER. A rule is reported N/A when
AFTER never occurs (the ordering was never put to the test), and AMBIG when one call
matched both sides — neither fails the run.

Needles are substrings of the *whole* tool input, paths included, so a loose needle
like "test" also matches any file under a directory containing "test". If a rule comes
back AMBIG, make one side more specific (e.g. `Write~/tests/` rather than `Write~test`).

Exit code: 0 if no rule FAILED, 1 otherwise.

Scope note: this checks *ordering only*, deliberately. Deciding whether a call
satisfies a spec step is meaning-based work for the model (see the skill's step 4);
a regex verdict here would silently disagree with it.
"""

import argparse
import json
import sys


def parse_matcher(text):
    for sep in ("=", "~"):
        if sep in text:
            name, _, needle = text.partition(sep)
            return name.strip(), needle.strip().lower()
    return text.strip(), None


def matches(call, name, needle):
    if name and call.get("name") != name:
        return False
    if needle is None:
        return True
    haystack = (call.get("detail", "") + " " + json.dumps(call.get("input", ""))).lower()
    return needle in haystack


def first_index(calls, matcher):
    name, needle = parse_matcher(matcher)
    for call in calls:
        if matches(call, name, needle):
            return call["n"]
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(prog="check-order.py")
    parser.add_argument("rules", nargs="+", help='"BEFORE:AFTER" ordering rules')
    parser.add_argument("--trace", help="trace JSON file (default: stdin)")
    args = parser.parse_args(argv)

    if args.trace:
        with open(args.trace, encoding="utf-8") as handle:
            raw = handle.read()
    else:
        raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"could not read trace JSON ({exc}) — pipe `extract-trace.py --json` in",
              file=sys.stderr)
        return 2

    calls = data.get("calls", data if isinstance(data, list) else [])
    if not calls:
        print("(timeline is empty — nothing to check)")
        return 1

    failed = False
    for rule in args.rules:
        if ":" not in rule:
            print(f"[SKIP] {rule} — expected BEFORE:AFTER")
            continue
        before_m, _, after_m = rule.partition(":")
        before, after = first_index(calls, before_m), first_index(calls, after_m)
        if after is None:
            verdict, note = "N/A ", f"'{after_m}' never occurred"
        elif before is None:
            verdict, note = "FAIL", f"'{before_m}' never occurred, but '{after_m}' did (@{after})"
            failed = True
        elif before == after:
            # One call satisfied both sides — the matchers don't discriminate, so there is
            # no ordering to judge. Reporting this as FAIL would be a confident wrong verdict
            # (a substring like "test" also matches any path containing it).
            verdict, note = "AMBIG", (f"both sides matched the same call @{before} — "
                                      f"narrow one matcher (needles are substrings of the "
                                      f"whole input, paths included)")
        elif before < after:
            verdict, note = "PASS", f"@{before} before @{after}"
        else:
            verdict, note = "FAIL", f"@{before} came after @{after}"
            failed = True
        print(f"[{verdict}] {rule:52s} {note}")

    print(f"\n{len(calls)} tool calls checked — {'FAILURES PRESENT' if failed else 'all satisfied rules passed'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
