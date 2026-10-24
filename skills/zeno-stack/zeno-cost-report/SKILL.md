---
name: zeno-cost-report
description: >
  Summarize local agent-harness spend by day, model, and session from the Stop-hook cost-tracking
  metrics log — a report over what the tracker already wrote, never a metering system itself.
  Trigger on: "cost report", "how much have I spent", "spend by model", "token cost this week",
  "export cost data".
---

# Cost Report

Summarize local spend by day, model, and session from the metrics log the harness's own Stop hook
writes. This is a report, not a metering system: it reads what the tracker wrote, it doesn't write
that file itself.

## Where the data lives

The cost-tracking Stop hook appends one JSON object per session-stop to a local metrics log. Each
row is a **cumulative snapshot for that session**, so the report takes the **latest row per
session id** and sums across sessions — summing every row would multiply-count.

Row schema: `{ timestamp, session_id, transcript_path, model, input_tokens, output_tokens, cache_write_tokens, cache_read_tokens, estimated_cost_usd }`

## What this does

1. Check the metrics log exists. If not, the tracker hasn't run yet — it only writes on a
   session's first Stop event, so a brand-new install has no data until then.
2. Reduce rows to the latest snapshot per session and aggregate.
3. Present a compact report (today / yesterday / total / by-model / last-7-days), or export recent
   rows as CSV on request.

Rely on the tracker's precomputed `estimated_cost_usd` values; don't re-estimate pricing from raw
tokens in the report itself — that's the tracker's job, not the report's.

## Report shape

1. Summary: today, yesterday, total, session count.
2. By model: models ranked by total cost.
3. Last seven days: date and cost.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Summing every row in the log | Take the latest row per session id first — rows are cumulative snapshots |
| Re-deriving cost from raw token counts | Use the tracker's own `estimated_cost_usd` — it's the source of truth |
| Erroring when the log doesn't exist yet | Report plainly that the tracker hasn't fired a Stop event yet |
| Treating this as the metering system | It's read-only over what the tracker already wrote |

## Pre-flight checklist — run before delivering any cost report

- [ ] Rows reduced to latest-per-session before aggregating, not summed raw.
- [ ] Missing/empty log handled with a plain explanation, not an error.
- [ ] Cost figures come from the tracker's own `estimated_cost_usd`, not re-derived here.
- [ ] Report includes today/yesterday/total, by-model, and last-7-days sections.
