#!/usr/bin/env bash
# Zeno Stop hook — appends one cumulative cost/token snapshot per session to
# ~/.claude/metrics/costs.jsonl, in the schema commands/cost-report.md already documents and
# reads (timestamp, session_id, transcript_path, model, input_tokens, output_tokens,
# cache_write_tokens, cache_read_tokens, estimated_cost_usd). /cost-report takes the latest row
# per session_id, so re-summing the whole transcript on every Stop is the correct, simple design.
#
# Never blocks the stop and never crashes the session: any failure here (missing transcript,
# unreadable JSON, unknown model) is swallowed and the hook exits 0 with no output. A broken cost
# tracker must not be able to interrupt normal Claude Code operation.
#
# Requires python3 for safe JSON parsing. Without it, this hook is a no-op (writing partial/
# malformed rows from hand-rolled bash JSON parsing would corrupt costs.jsonl, which is worse than
# not logging that session at all).

if ! python3 -c '' >/dev/null 2>&1; then
  exit 0
fi

# Capture the hook's stdin payload into a variable BEFORE invoking python3 — a `python3 <<'PY'`
# heredoc uses stdin to feed the script itself, so `json.load(sys.stdin)` inside the heredoc
# would read nothing (or the heredoc text). Pass the payload through an env var instead, same
# pattern zeno-session-start.sh already uses for its own inputs.
HOOK_PAYLOAD="$(cat)"

HOOK_PAYLOAD="$HOOK_PAYLOAD" python3 <<'PY' 2>/dev/null
import json, os, sys, datetime

def main():
    try:
        payload = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
    except Exception:
        return
    session_id = payload.get("session_id") or "unknown"
    transcript_path = payload.get("transcript_path")
    if not transcript_path or not os.path.isfile(transcript_path):
        return

    # Pricing per model, USD per million tokens: (input, output). Cache write/read are derived
    # from the input rate (5m write = 1.25x, 1h write = 2x, read = 0.1x), per Anthropic's
    # published cache pricing mechanics.
    #
    # Effective-dated per model: a list of (effective_date, input, output) tuples in ascending
    # date order. rate_for() below picks the latest tier whose effective date has passed. This
    # replaced a single static tuple + a comment reminder after that reminder went unnoticed for
    # 3 days (Sonnet 5's $2/$10 introductory rate was already known to revert to $3/$15 on
    # 2026-09-01 when this hook was first written, but nothing would have applied that change
    # automatically). Re-check https://www.anthropic.com/pricing before trusting
    # estimated_cost_usd for budgeting decisions regardless — this is directionally useful, not
    # authoritative, and unknown future changes still require a manual tier append.
    PRICING = {
        "claude-sonnet-5": [
            ("2026-08-08", 2.0, 10.0),   # introductory rate, in effect when this hook was written
            ("2026-09-01", 3.0, 15.0),   # confirmed revert date
        ],
        "claude-haiku-4-5-20251001": [("2026-08-08", 1.0, 5.0)],
        "claude-haiku-4-5":          [("2026-08-08", 1.0, 5.0)],
        "claude-opus-5":             [("2026-08-08", 15.0, 75.0)],
        "claude-opus-4-8":           [("2026-08-08", 15.0, 75.0)],
        "claude-fable-5":            [("2026-08-08", 3.0, 15.0)],
    }
    DEFAULT_PRICING = [("2026-08-08", 3.0, 15.0)]  # unrecognized model id — conservative mid-tier estimate

    def rate_for(model, iso_date):
        # Exact id first, then longest matching prefix — a date-suffixed id like
        # "claude-sonnet-5-20260301" must hit the sonnet tiers, not DEFAULT_PRICING
        # (that fall-through overstated the introductory 2.0/10.0 rate as 3.0/15.0).
        tiers = PRICING.get(model)
        if tiers is None:
            for key in sorted(PRICING, key=len, reverse=True):
                if model.startswith(key):
                    tiers = PRICING[key]
                    break
        if tiers is None:
            tiers = DEFAULT_PRICING
        applicable = [t for t in tiers if t[0] <= iso_date]
        chosen = applicable[-1] if applicable else tiers[0]
        return chosen[1], chosen[2]

    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_5m": 0,
        "cache_1h": 0,
        "cache_unbrokenized": 0,   # cache_creation_input_tokens with no breakdown dict
    }
    last_model = None

    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                msg = obj.get("message")
                if not isinstance(msg, dict) or msg.get("role") != "assistant":
                    continue
                usage = msg.get("usage")
                if not isinstance(usage, dict):
                    continue
                totals["input_tokens"] += int(usage.get("input_tokens") or 0)
                totals["output_tokens"] += int(usage.get("output_tokens") or 0)
                totals["cache_creation_input_tokens"] += int(usage.get("cache_creation_input_tokens") or 0)
                totals["cache_read_input_tokens"] += int(usage.get("cache_read_input_tokens") or 0)
                creation = usage.get("cache_creation")
                written = int(usage.get("cache_creation_input_tokens") or 0)
                if isinstance(creation, dict):
                    totals["cache_5m"] += int(creation.get("ephemeral_5m_input_tokens") or 0)
                    totals["cache_1h"] += int(creation.get("ephemeral_1h_input_tokens") or 0)
                elif written:
                    # No per-TTL breakdown on this row. Price the write at the 5m rate rather
                    # than at zero — the row already reports these tokens as cache_write_tokens,
                    # so charging nothing for them silently understated every such session.
                    totals["cache_unbrokenized"] += written
                model = msg.get("model")
                if model:
                    last_model = model
    except Exception:
        return

    if last_model is None:
        return  # no assistant turns with usage found — nothing to log

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    in_rate, out_rate = rate_for(last_model, today)
    mtok = 1_000_000.0
    cost = (
        totals["input_tokens"] / mtok * in_rate
        + totals["output_tokens"] / mtok * out_rate
        + totals["cache_5m"] / mtok * in_rate * 1.25
        + totals["cache_1h"] / mtok * in_rate * 2.0
        + totals["cache_unbrokenized"] / mtok * in_rate * 1.25
        + totals["cache_read_input_tokens"] / mtok * in_rate * 0.1
    )

    row = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": session_id,
        "transcript_path": transcript_path,
        "model": last_model,
        "input_tokens": totals["input_tokens"],
        "output_tokens": totals["output_tokens"],
        "cache_write_tokens": totals["cache_creation_input_tokens"],
        "cache_read_tokens": totals["cache_read_input_tokens"],
        "estimated_cost_usd": round(cost, 6),
    }

    try:
        metrics_dir = os.path.expanduser("~/.claude/metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        with open(os.path.join(metrics_dir, "costs.jsonl"), "a", encoding="utf-8") as out:
            out.write(json.dumps(row) + "\n")
    except Exception:
        return

main()
PY

exit 0
