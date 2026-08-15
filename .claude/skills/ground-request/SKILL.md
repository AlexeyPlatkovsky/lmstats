---
name: ground-request
description: Checks whether asserted content's premise holds before anything records it as project state — locates each asserted subject in project documentation first and source second, classifies each subject, and blocks the write when a premise cannot be confirmed.
user-invocable: true
---

# Ground Request

## Responsibility

Check the premise of content bound for project state — a raw user request or the agent's own analysis
— before any artifact records it. Produce a grounding outcome per asserted subject, the evidence
behind it, and the open questions the content leaves unanswered.

This capability is a skill rather than an agent because outcome `unverified` stops and asks the user
and gap disclosure discusses the request with the user, so it cannot run to completion in an isolated
context.

`.claude/conventions/documentation-quality.md` owns the standards applied here: Evidence Boundary for
unverified claims, Gap Disclosure for proposed work.

## Layer boundary

This skill reads, classifies, and reports. It writes nothing. Do not use it to:

- classify or route the work — use `.claude/skills/manager/SKILL.md`;
- write or update TaskPilot items — use `.claude/skills/track-with-taskpilot/SKILL.md`;
- repair documentation it finds stale — use `.claude/skills/maintain-docs/SKILL.md`.

## When to use

Whenever a user request or the agent's own analysis would be written into a TaskPilot item title,
description, or comment body. Exempt only when the content is derived from an **unqualified**
statement in an already-accepted specification — a statement disqualified under the marker or register
rules in `.claude/conventions/documentation-quality.md` is not a grounding exemption, and an accepted
specification may contain both. Being invoked inline by a pipeline is not an exemption.

Requirements, specification statements, and documentation claims are subject to the same Evidence
Boundary standard, but no capability currently gates them through this skill; see Gaps below.

## Evidence order

Documentation answers *what* the behavior is. Source decides *whether* it exists.

1. Consult `docs/INDEX.md` to identify the smallest document that owns the subject and read that
   document only. Do not load the `docs/` tree wholesale — selective loading is why the index exists.
   `.claude/conventions/documentation-quality.md` owns which documents count as evidence and which
   record only intent; a document outside the recording set never grounds a presence claim.
2. The owning document records the subject as delivered, unqualified behavior → it supplies the
   semantics of the claim, and rule 5 still applies.
3. A statement disqualified under `documentation-quality.md` — `[planned]`, `[not implemented]`,
   `[superseded: <ref>]`, `(future)`, `⏳`, the "shall"/"should"/"could" register, or equivalent
   deferring wording — does not ground the claim. Decide the outcome from source under rule 5; a
   disqualified statement that source turns out to confirm is outcome 3, and a documentation defect
   unless `documentation-quality.md` exempts that disqualifier — not an absence.
4. The owning document is silent → silence is evidence of nothing. Report a documentation **gap**
   naming the document that should own the answer, and continue to source.
5. Run the source search for the asserted token regardless of what the documentation said — one
   targeted search for a presence assertion, or the two searches under "Locating the subject" for an
   absence assertion.
   This is the step that makes a stale document detectable: when documentation and source disagree,
   source is the fact, the document is defective, and the correction plus a documentation **defect**
   is reported. Grounding a claim on a document alone would leave every doc defect invisible.
6. An assertion that a subject is *absent* is never confirmed by documentation. Documents omit
   routinely; only source can establish an absence.

"Source" here means the implementation and its configuration: `src/`, `web/`, `tests/`, `scripts/`,
and packaging or config files. Instruction artifacts under `.claude/` and `.manifesto/` are not
source — a token that appears only in a skill or pipeline file, including an example inside this one,
is not evidence that the product has it.

Grounding evidence never comes from `.taskpilot/` items, other backlog items, or conversation
history. An unverified item must not become the evidence that grounds the next one.

This is a premise check, not an investigation: one targeted search per asserted token is enough for a
presence assertion. Confirming a premise here does not replace verification at implementation time.

## Locating the subject

Search for the most specific literal token the request asserts — a file, symbol, command, flag,
setting, route, or config key. When the request asserts several, each must be located; one unlocated
token is enough for outcome 1. When the assertion is behavioral rather than a named token, search for
the nearest implementing symbol, file, or literal value the assertion names.

An absence assertion ("there is no validation for empty titles") needs two searches: the module the
request's own terms name, and the domain model, schema, or service that would enforce the behavior —
enforcement often lives in a field type rather than in code that repeats the request's wording. When
the second search cannot be aimed, record outcome 1 rather than confirming the absence.

Both absence searches are source searches. Documentation never participates in an absence check
(Evidence order rule 6), so a document's silence contributes nothing here.

## Outcomes

Outcomes 1-3 apply to a subject the asserted content presents as already present. A subject it makes
no assertion about is outcome 4. An absence assertion resolves under the absence rule below, which
can also yield outcome 1 — when its second search cannot be aimed — or outcome 2, when either search
locates the subject; an unconfirmed absence is never recorded as outcome 4. Within outcomes 1-3,
record the first that applies; once the asserted subject is located, outcome 1 no longer applies.

1. `unverified` — the asserted content presents a subject as already existing and source does not
   locate it. Stop and ask the user, reporting which search failed — or, when no search target could
   be named, reporting that instead. The caller must not write this subject.

   A user answer is a recorded input on re-run, not a reason to repeat the search. A restatement that
   supplies new evidence is grounded normally against that evidence. A confirmation supplying no new
   evidence resolves the subject as `unverified, user-confirmed`: the write may proceed and requires a
   `needs triage` marker naming what could not be verified, the search that failed, and the fact that
   the user confirmed it anyway. The calling capability owns how that marker is recorded.
2. `partially grounded` — the subject is located but a detail of the assertion is wrong. Report the
   located state so the caller writes that, not the state asserted.
3. `grounded` — subject located and accurately described. Report the citation.
4. `new scope` — the asserted content says nothing about current repository state, or asserts an absence
   that source confirmed. It describes work that does not exist yet.

For an absence assertion: if either search locates the subject, the assertion is wrong — outcome 2,
carrying the located state. If neither locates it, the absence is confirmed and the subject is
outcome 4.

When one subject carries both a presence and an absence assertion, evaluate each assertion separately
and record, for that subject, the strictest outcome that applies (1 over 2 over 3 over 4). Report
every correction the absence check produces even when the recorded outcome comes from the presence
assertion. This rule never authorizes a write that outcome 1 refuses, and it never changes the
outcome of a different subject.

Illustrative example (adds no requirements): "`--ask-for-approval` should be replaced with
`--dangerously-bypass-approvals`" presents the first flag as in use, so it is outcome 1 until that
flag is located — even though performing the replacement would be new work. By contrast, "add a
dark-mode toggle" asserts nothing about current state and is outcome 4.

Grounding is per subject, not per request. A request naming several subjects yields an outcome for
each, and a blocked subject does not suppress the grounded ones.

## Gap disclosure for proposed work

Applies to every request proposing work not yet done, whatever its grounding outcome, when it leaves
material gaps as defined in `.claude/conventions/documentation-quality.md` Gap Disclosure. A request
can be `grounded` — its subject located and accurately described — and still propose an undecided
change; "add a toggle to hide the Cancelled column" names a column that exists, so it is outcome 3,
and its open questions still need answers.

Discuss the gaps with the user before this skill's artifact closes, unless the user has explicitly
deferred that discussion to implementation time. Deferral waives the discussion only; the gaps are
still recorded and reported. For an outcome-1 subject, carry its gaps into the question outcome 1
already requires rather than asking twice.

Run one consolidated gap pass per user request, not one exchange per subject. A request naming seven
subjects produces one set of questions, not seven rounds.

## Output Contract

The artifact begins with `Skill: ground-request - output below` and reports:

- status (`completed` or `blocked`) — `blocked` when any subject resolved to `unverified` and remains
  unconfirmed; a subject resolved to `unverified, user-confirmed` is `completed`;
- per asserted subject: the outcome, the searches run, and the evidence path or the search that
  failed; for a confirmed absence, both searches that established it;
- corrections the caller must apply for any `partially grounded` subject;
- documentation gaps and defects found, each naming the document that should own the answer;
- open questions raised for the user, and whether discussion was deferred;
- blockers.

Always emit the artifact. It is the evidence a calling capability's write gate requires.

## Gaps

Recorded per `.claude/conventions/documentation-quality.md` Gap Disclosure rather than left implicit:

- Only TaskPilot item writes are gated through this skill. `spec-driven-development` and
  `maintain-docs` write project state from user requests and name no grounding artifact, so a false
  premise entering a specification statement or a documentation claim is unguarded. Closing that
  needs a gate in each of those skills, which is a separate routed change.
- The manager performs no subject-existence check during classification, so a request whose premise
  is false can still be routed to an implementation pipeline that never reaches this skill. Deferred
  by explicit user decision.
