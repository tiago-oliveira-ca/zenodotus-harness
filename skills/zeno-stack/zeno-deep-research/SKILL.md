---
name: zeno-deep-research
description: >
  Multi-source deep research — firecrawl/exa MCP tools when configured, otherwise the built-in WebSearch/WebFetch fallback (same method, less crawl depth) — decomposes a topic
  into sub-questions, searches and deep-reads multiple sources, and synthesizes a cited
  report with a sources list and explicit confidence/gaps. Use for thorough research
  requiring evidence and citations: competitive analysis, technology evaluation, market
  sizing, due diligence, or any "what's the current state of X" question. Trigger on:
  "research", "deep dive", "investigate", "what's the current state of", "competitive
  analysis", "due diligence", or any request needing synthesis from multiple cited
  sources rather than a single quick lookup.
---

# Deep Research

Produce a thorough, cited research report by decomposing a topic, searching multiple
sources via firecrawl/exa MCP tools, deep-reading the strongest ones, and synthesizing
findings with explicit source attribution.

> **Drift-prone surface.** MCP tool names, quotas, and result shapes for firecrawl/exa
> change over time. Verify the configured MCP tools and current docs before promising
> coverage or quoting live source counts.

## Tooling (MCP preferred, built-in fallback always available)

At least one of:
- **firecrawl** — `firecrawl_search`, `firecrawl_scrape`, `firecrawl_crawl`
- **exa** — `web_search_exa`, `web_search_advanced_exa`, `crawling_exa`

Both together give the best coverage; either alone is workable. Configure in
`~/.claude.json` or the equivalent MCP config.

**Fallback tier — no MCP server configured.** If neither firecrawl nor exa is available
(check before starting, don't discover it mid-run), run the same workflow on the built-in
`WebSearch` (breadth) and `WebFetch` (deep-reads) tools: same decomposition, same 15-30-source
target, same deep-read-the-strongest-3-5 rule, same citation/confidence standards. The loss is
crawl depth and structured extraction, not method — note "built-in tools, no crawl tier" in the
report's methodology line so the reader can calibrate. Never dead-end on the missing servers.

## Workflow

**1. Clarify the goal.** Ask 1-2 quick questions — "what's your goal: learning, deciding,
or writing something?", "any specific angle or depth?" If the user says "just research
it," proceed with reasonable defaults instead of blocking on this.

**2. Decompose into 3-5 sub-questions.** E.g. "impact of AI on healthcare" splits into:
main applications today, measured clinical outcomes, regulatory challenges, leading
companies, market size/trajectory.

**3. Search each sub-question across sources.** Use 2-3 keyword variations per
sub-question, mixing general and news-focused queries. Target 15-30 unique sources total.
Prioritize academic/official/reputable-news over blogs, and blogs over forums.

```
firecrawl_search(query: "<sub-question keywords>", limit: 8)
web_search_exa(query: "<sub-question keywords>", numResults: 8)
web_search_advanced_exa(query: "<keywords>", numResults: 5, startPublishedDate: "2025-01-01")
```

**4. Deep-read the strongest 3-5 sources in full** — don't synthesize from search
snippets alone.

```
firecrawl_scrape(url: "<url>")
crawling_exa(url: "<url>", tokensNum: 5000)
```

**5. Synthesize into a structured report:**

```markdown
# [Topic]: Research Report
*Generated: [date] | Sources: [N] | Confidence: [High/Medium/Low]*

## Executive Summary
[3-5 sentence overview of key findings]

## 1. [First Major Theme]
- Key point ([Source Name](url))
- Supporting data ([Source Name](url))

## 2. [Second Major Theme]
...

## Key Takeaways
- [Actionable insight 1]
- [Actionable insight 2]

## Sources
1. [Title](url) — [one-line summary]

## Methodology
Searched [N] queries across web and news. Analyzed [M] sources. Sub-questions: [list]
```

**6. Deliver.** Short topics: post the full report in chat. Long reports: post executive
summary + key takeaways, save the full report to a file.

## Parallelizing broad topics

For wide-scope topics, split sub-questions across parallel agents (e.g. via the Agent
tool) — one agent per 1-2 sub-questions, each independently searching and reading, with
the calling session synthesizing all returned findings into the final report.

## Quality rules

1. **Every claim needs a source** — no unsourced assertions.
2. **Cross-reference** — a claim backed by only one source gets flagged as unverified.
3. **Recency matters** — prefer sources from the last 12 months unless historical context
   is the point.
4. **Acknowledge gaps** — if a sub-question turned up nothing solid, say so explicitly
   rather than papering over it.
5. **No hallucination** — "insufficient data found" beats a fabricated answer.
6. **Separate fact from inference** — label estimates, projections, and opinions as such.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Synthesizing from search snippets only | Deep-read the 3-5 strongest sources in full |
| One source backing a load-bearing claim | Cross-reference; flag single-source claims as unverified |
| Silently skipping a sub-question with no good results | State the gap explicitly in the report |
| Presenting estimates as measured fact | Label projections/opinions distinctly from sourced fact |
| Reporting stale sources without noting recency | Prefer last-12-months sources; note when older sources are the best available |
| Skipping the clarifying question on an ambiguous ask | Ask 1-2 quick questions unless the user says "just research it" |

## Pre-flight checklist — run before delivering any research report

- [ ] Topic was decomposed into 3-5 concrete sub-questions before searching
- [ ] 15-30 unique sources were searched; 3-5 strongest were deep-read in full
- [ ] Every claim in the report traces to a cited source
- [ ] Single-source claims are flagged as unverified rather than stated as fact
- [ ] Gaps (sub-questions with weak/no evidence) are stated explicitly, not hidden
- [ ] Report includes Executive Summary, themed sections, Key Takeaways, Sources, and Methodology
- [ ] Delivery format (inline vs. file) matches report length
