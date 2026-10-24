---
name: zeno-model-route
description: >
  Thin router for model-tier selection — the shape × risk heuristic itself lives in the
  /model-route command (the lane owner per CLAUDE.md's Config-maintenance table); this stub
  exists so zeno-stack routing resolves and as the Codex-target fold home for that command's
  content. Trigger on: "which model should I use", "model tier", "haiku or sonnet or opus",
  "cheapest model that can do this", "model routing".
---

# Zeno Model Route — router stub

**Claude Code target:** invoke the `/model-route` command — it owns the shape × risk routing
table, the `--budget` ceiling semantics, and the calibration loop against `/cost-report`.
This stub deliberately carries no copy of that heuristic (a second copy would drift).

**Codex target:** the build (`tools/codex/build_codex.py`, per `fold-map.toml`) appends the
command's full content below this line, so on Codex this skill *is* the heuristic.
