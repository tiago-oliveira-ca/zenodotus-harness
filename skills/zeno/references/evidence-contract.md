# Evidence contract — one claim, an observation, an honest result

Load this reference when accepting a disputed finding, recording completion evidence or deciding
whether a gate can close. Keep ordinary proof short and use the existing card's **Proof** section;
high-risk or disputed work gets more detail, not another workflow hierarchy.

Concept inspiration: [Uncle Bob's explicit governance outcomes](https://robert-hoffmann.github.io/uncle-bob/skills/ub-governance.html); this record format and its Zeno integration are original.

## Gate outcomes and evidence states

Gate outcomes are **pass**, **fail** or **blocked**. They describe the current evaluation; card
`Status` remains `backlog | development | testing | closed`. Do not add a stored pipeline-stage
field or infer a gate pass from a card's Status.

- **pass:** all required claims have applicable passing evidence and required review is complete.
- **fail:** a required check ran and demonstrated failure, or the declared record is invalid.
- **blocked:** required evidence, a prerequisite, freshness or an independent review is unavailable.

If failure and blockage coexist, report `fail` and list the blocked requirements too. Neither
result permits closure. Optional recommendations remain visible without acquiring a veto.

Each evidence record uses `pass | fail | blocked | not_run | not_applicable`. `not_run` means no
observation occurred; `blocked` names why it could not occur. Neither means success.
`not_applicable` needs a reason tied to the accepted scope; a quota-limited required review is
still applicable. Required claims come from acceptance criteria and the applicable gate, not
from choosing which checks are easiest to run.

## Proof record

Use this format for new closeout records; a single record may cover related claims established by
the same observation. Retain detailed RED/GREEN notes at Task/SubTask leaves and reference those
records from the parent. Historical cards need no bulk rewrite; normalize a selected old card only
when it is being evaluated under this contract.

```markdown
### E-install-safety
- Claim: The installer preserves unrelated skills on a repeat install.
- Required: yes
- Kind: check
- Result: pass
- Evidence: `bash tools/test_install.sh` → exit 0; unrelated sentinel unchanged.
- Revision: <commit or explicitly named working-tree content snapshot>
- Environment: <relevant OS, runtime and configuration>
- Owner: <who obtained the observation or must obtain it next>
```

`Kind` is `check` or `review`; evidence IDs are unique within the card. `Required` is `yes` or
`no`. A review record names its reviewer in Owner, its reviewed revision, and the finding/verdict
in Evidence. For `not_applicable`, add `- Reason: <why the accepted scope excludes this claim>`.
For blocked/not-run evidence, Evidence names the missing prerequisite or the actual error rather
than inventing output. Append a new record with a new ID when evidence changes. Add
`- Supersedes: E-<old-id>` to point at the earlier record for the same Claim; retain the old
observation as history. A supersession chain retains the same Claim, Required and Kind. It must
not cycle or refer to a missing ID. Only the latest
records in those explicit chains decide the current gate; an unrelated passing result does not
cancel a failed required claim.

## What an observation must establish

1. Name the accepted outcome, not merely an implementation step or invocation.
2. Record the actual command or observation and its observed result. A command's presence in a
   card does not mean it executed; a tool error before inference is not a behavioral eval result.
3. Bind the result to the relevant revision/content and environment. Re-run when a subsequent
   change affects the claim, or when the environment makes the earlier observation inapplicable.
4. Keep the evidence owner and location discoverable. Preserve IDs, unresolved findings, review
   availability and approvals in the existing Task-State handoff.
5. For a required independent pass, obtain the matching Advisor's opinion and inspect its evidence.
   A delegated success statement, self-review, or attempted invocation is not that pass.

Metadata cannot prove freshness or reviewer independence. The orchestrator still checks them
against the actual tools, revision and permissions; never accept a self-declared reviewer label
as a capability or approval grant.

## Exceptions and scope decisions

An exception records its owner, rationale, creation date, expiry/revisit date and follow-up in
**Decisions**. The human must approve a change to an accepted requirement or authorization before
it is applied. No exception overrides host permissions or higher-priority instructions. Preserve
failed observations as failed: when scope changes, record which claim is no longer required and
why. Keep `Required: yes` in its supersession chain and use `not_applicable` with a scope-specific
Reason for an approved exclusion, alongside the human decision. Preserve the earlier failure.

## Mechanical check versus Review

The skill-owned `scripts/check_lifecycle.py` checks explicitly selected cards and linked children.
Run it with Python from the installed `zeno` skill directory; it does not require this library's
maintainer-only `tools/`, CI or backlog. It reads records without executing their commands and
never modifies card Status. `--gate route` checks planning structure; `--gate review` checks
closeout records. Add `--require-review` when a matching Advisor is required for the selected item.

A checker **pass** means **card integrity only**. It is necessary record evidence, never proof
of factual truth, actual execution, freshness, reviewer independence, safety or human approval.
Keep all four gates and the real `zeno-verify` observations even when metadata is valid.

The report identifies its path-protection mode. Supported POSIX hosts use anchored no-follow
descriptor reads and reject non-regular files. The portable fallback verifies file and ancestor
identity before reading. Concurrent path replacement is unsupported in that fallback. Check a
stable local hierarchy there and retain this platform limit with the observation.
