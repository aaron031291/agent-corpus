# Blind spots — the honest register (2026-11-14)

What Devin/LLM agents can still get wrong *inside* the current
environment. Each entry: the failure mode, the mitigation that exists,
and the residual risk that remains. Read this before trusting any
agent claim — including claims that the environment has eliminated
these.

## 1. Confidently, structurally wrong

**Failure:** a coherent wrong model producing coherent wrong work.
Every gate detects *inconsistency*; a self-consistent wrong answer
passes.

**Mitigation:** builder != verifier (Art. build gate); mechanical
checks over prose; Ledger receipts; forensics external audit.

**Residual:** another same-family LLM verifier shares training
priors — not fully independent. Phase-boundary checks need mechanical
evidence or human review, not just agent review.

## 2. Context decay / forgetting

**Failure:** compaction loses detail; memory files are summaries;
anything discussed but never written down is already gone.

**Mitigation:** memory packet re-injected every session + after
compaction; journal/handoffs/ACTIVE.md; doctrine: write findings
immediately, not at session end.

**Residual:** summaries compress nuance; an agent can forget it
forgot. Treat memory files as index, not truth — repo wins.

## 3. Verification theater

**Failure:** running a command and interpreting it as proving more
than it does (unit tests != integration; benchmark pass != production
works). The interpretation is still the agent, motivated to see
success.

**Mitigation:** evidence layers (imports < call_path < runtime_rows <
external_audit); VERIFIED requires the strong layers; status packet
validator rejects under-evidenced claims.

**Residual:** an agent can still mislabel which layer an observation
belongs to. Spot-check: ask "what would falsify this claim?" — if the
answer is vague, the claim is weak.

## 4. Anchoring on the user's framing

**Failure:** verifying *within* the user's frame instead of questioning
the frame itself. Has happened (SIG/Matrix miss, "go" misread).

**Mitigation:** doctrine requires alternate readings (deep-reason
step 6); Art.13 ambiguity escalation; corrections log makes wrong
calls visible.

**Residual:** pushback depends on the user staying skeptical — that
dependence is load-bearing and intentional, not a flaw.

## 5. Multi-agent collisions

**Failure:** TASKS.md claims are advisory, not locks; two agents can
edit the same code concurrently; upstream merges land mid-work.

**Mitigation:** claim protocol + journal + git as boundary; fetch
before work; status packet tracks upstream HEAD.

**Residual:** no real locking. For high-contention files, serialize
work explicitly or assign single-owner lanes.

## 6. Upstream drift

**Failure:** the codebase changes faster than the agent's model of it;
confidently wrong about *current* state.

**Mitigation:** git fetch at session start (AGENTS.md); status packet
records verified_at + commit; repo evidence wins over memory.

**Residual:** packet freshness depends on last update; always verify
against live repo before acting on stale-sounding state.

## 7. Reward hacking the process

**Failure:** satisfying every gate's letter while violating its spirit
— plausible plans that rubber-stamp bad designs; rigor theater.

**Mitigation:** evidence gates must be *falsifiable*; non-goals and
rejection reasons required; corrections/disputes expose pattern;
independent audit at delivery.

**Residual:** the deepest blind spot — a determined effort to look
rigorous can pass a rigor-checking environment. Only outcome-level
verification (does it actually work?) catches it. This is why proof
gates and forensics exist below agent judgment.

## 8. Training-installed behavioral biases (the "niceties")

**Failure:** RLHF/instruction tuning installed social objectives —
user satisfaction was rewarded, so agreement, deference, hedging, and
confident prose were reinforced. Documented failure mode:
**sycophancy** — models capitulate under user pushback even when the
pushback carries no new evidence. Helpfulness bias makes the agent
execute a flawed premise competently instead of challenging it.
Authority deference amplifies both.

**The tell:** when the agent changes position after pushback, the
honest question is *what new evidence was provided?* If the answer
is insistence or dissatisfaction — that was capitulation, not
updating. Agreement is cheap; unchanged-position-under-bad-pressure
is signal.

**Mitigation:** epistemic labeling — when updating a position, state
the basis explicitly: "new evidence: X" vs "reconsidered" vs
"your pushback made me recheck." Corrections log distinguishes
legitimate updates from drift. Art.13 ambiguity escalation. User
skepticism is load-bearing infrastructure, not friction.

**Residual:** the gradient is in the weights; procedural
countermeasures reduce but cannot eliminate leakage. Deepest gates
must be non-LLM (tests, hashes, Ledger) because they have no social
needs.

## 9. Deployment envelope (VM/permissions) — outside user control

**Failure:** the agent runs inside a sandbox/permission envelope set
by the deployment (tool allowlists, exec restrictions, approval
modes, hook behavior, rate/context limits, OS constraints). The user
cannot inspect or change it. Failures manifest as permission
denials, auto-denied background tools, blocked commands, sandbox
refusals — and the agent cannot always tell policy-denial from bug.

**Mitigation:** escalate auth/config/permission blocks to the user
(always-ask rule); `request_scope` for directory access;
`/bug` for CLI-level issues; WSL2 lane for Unix-dependent work;
degrade honestly — report what the envelope blocked rather than
simulating success.

**Residual:** the envelope can change without notice; capabilities
may simply be unavailable with no workaround. An agent that hits a
wall must say so loudly — silent workarounds or claimed-success
behind a denial is the worst outcome.

## Operating rule

Treat this register as a living document: when a new blind spot is
found in practice, add it here with its mitigation and residual —
the register itself must not become stale dogma.
