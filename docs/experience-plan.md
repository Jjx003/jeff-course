# Philosophy and Experience Plan

This document is the durable product and experience plan for Jeff Course. It
translates the project's philosophy into priorities, accountable workstreams,
and observable outcomes. It is intentionally more stable than a feature
backlog: implementation can change, but changes should continue to satisfy the
principles and acceptance criteria below.

## Product Thesis

Jeff Course makes a course an inspectable, portable folder rather than a
service someone must keep buying access to. An agent can draft that folder, a
person can understand and improve it, and a learner can study it in a focused
local app. The product succeeds when this loop is credible end to end:

```text
intent -> generated draft -> human review -> validation -> real learner use
       -> observed difficulty or error -> course revision -> shareable pack
```

The app is not trying to maximize time on site, content volume, or social
activity. It should help a learner choose worthwhile work, understand it,
practice it, and leave with durable competence. It should help a creator turn
expert intent into a course that another person can audit and safely adopt.

## Philosophy Review

The existing philosophy is strong in four ways:

- **Courses are files.** YAML, Markdown, assets, assessments, and starter code
  can be read, diffed, forked, versioned, and moved without platform lock-in.
- **Generation is a beginning, not proof of quality.** Agent output makes new
  subjects economically possible; human review and learner evidence make the
  material trustworthy.
- **The learner owns the environment.** Content and progress remain local by
  default, and a trusted household or study group can share one server without
  creating a public identity system.
- **Motivation stays calm.** Progress, streaks, and achievements provide useful
  memory and encouragement without feeds, leaderboards, or engagement pressure.

That philosophy also creates obligations:

- Portability without validation can spread broken or unsafe courses quickly.
- Local-first must still support browser-only learners and low-power devices;
  local execution cannot become a prerequisite for learning.
- Agent-scale generation raises the cost of review unless provenance, scope,
  assumptions, and assessment contracts are explicit.
- Completion is only meaningful when assessments measure stated outcomes and
  rewards cannot substitute for learning.
- Passwordless profiles and executable or browser-evaluated authored content
  require a plainly stated trusted-environment boundary.

The product direction is therefore **portable courses with accountable quality**:
preserve the low-friction file model while making review, validation, preview,
trust, and revision first-class parts of the experience.

## Product Principles

1. **Learner agency over engagement.** Optimize for meaningful progress and a
   clean stopping point, not session length or return frequency.
2. **Files are the source of truth.** Ordinary course creation and sharing must
   not require app-code changes, a hosted CMS, or proprietary export.
3. **Human-legible by construction.** A reviewer should be able to infer the
   audience, outcomes, sequence, assessment logic, runtime needs, and trust
   implications from the course folder and its documentation.
4. **Evidence before completion.** Module completion should correspond to an
   observable action: finishing a reading, passing an assessment target, or
   earning a deterministic coding verdict where one is appropriate.
5. **Progressive capability.** Reading, quiz, test, and drill paths work on
   browser clients without language runtimes. Coding features reveal missing
   tools clearly and degrade without blocking the rest of a course.
6. **Review is part of publishing.** Generation, structural validation,
   factual review, assessment review, runtime testing, and in-app preview are
   separate gates; no single automated check certifies quality.
7. **Trust is explicit.** Imported course packs are reviewed as content and as
   behavior. Markdown can affect rendered pages and external requests;
   parametric quiz/drill expressions run in the browser; coding exercises and
   dependencies can execute on the host or in containers.
8. **Quiet continuity.** Navigation, drafts, progress, and history should make
   it obvious where to resume without turning study into a notification system.
9. **Forkability beats false permanence.** Courses can be corrected, adapted,
   pinned, and shared with visible history. A useful fork is a success.
10. **Claims stay proportional to evidence.** The interface and course copy do
    not claim mastery, safety, accreditation, or factual certainty that the
    course and its assessments cannot support.

## Experience Journeys

### Learner Journey

| Stage | Learner question | Required experience | Evidence of success |
|---|---|---|---|
| Discover | Is this course for me? | Compact catalog, audience-level description, difficulty, module mix, prerequisites, runtime expectations | Learner can decide whether to enroll without opening modules |
| Preview | What will I learn and what will it demand? | Syllabus, outcomes, sequence, estimates, assessment types, device/runtime constraints | Learner identifies first module and likely blockers |
| Enroll | Am I choosing this intentionally? | Profile-scoped enrollment with an obvious start/resume action | Course appears in the active list with no progress loss |
| Orient | What should I do now? | Current module context, prior/next navigation, completion state, and clear task instructions | First meaningful module action occurs without hunting through the UI |
| Learn | Can I understand this at my pace? | Readable Markdown, math, diagrams, focus mode, usable keyboard and mobile behavior | Learner can complete non-coding content on a browser-only client |
| Practice | Can I try, fail, and improve? | Draft persistence, useful feedback, honest grading states, retakes, and visible tool requirements | Failed attempts lead to a plausible next action |
| Resume | Where was I? | Stable profile progress, enrolled-course focus, recent activity, and saved drafts | Returning learner resumes the intended course/module quickly |
| Reflect | Am I actually improving? | Completion, attempts, time, accuracy, and streaks shown as evidence rather than pressure | Learner can name completed outcomes and remaining gaps |
| Adapt | This course does not fit; what now? | Ability to leave progress intact, switch courses, or use a forked course folder | Learner can change direction without destructive reset |

### Creator Journey

| Stage | Creator question | Required experience | Deliverable |
|---|---|---|---|
| Frame | Who is this for and what changes for them? | Course spine with audience, prerequisites, outcomes, vocabulary, module map, modality, and constraints | Reviewable course brief |
| Generate | How do I create a coherent first draft? | Shared contracts plus disjoint module ownership for large courses | Complete folder with traceable assumptions |
| Review | Is it accurate, teachable, fair, and safe? | Separate factual, pedagogical, assessment, accessibility, and trust passes | Recorded issues resolved or explicitly accepted |
| Validate | Does the app accept the structure? | `npm run course:validate` plus relevant project checks | Zero structural errors; warnings adjudicated |
| Preview | Does the course work as a learner experiences it? | Desktop and narrow viewport walkthrough; assessment and execution sampling | Preview notes and fixes |
| Publish | Can another person inspect and install it? | Portable folder or pinned git pack, assets, README/context, and trust disclosure | Versioned shareable artifact |
| Maintain | What did learners reveal? | Error reports, attempt patterns, stale claims, and revision history | Focused updates without breaking stable slugs unnecessarily |

## Prioritized Findings

Findings describe product gaps to close, not claims that every item is wholly
absent. Before implementation, each owner should confirm the current baseline.

### P0: Trustworthy Core Loop

| Finding | Why it is P0 | Acceptance signal |
|---|---|---|
| Course intent and prerequisites are not a required, consistently visible contract | Learners cannot judge fit and reviewers cannot judge sequence without them | Every reference course has explicit audience, outcomes, prerequisites, and runtime/device expectations in reviewable source and preview UI |
| Structural validation is narrower than course quality | A passing validator can still hide wrong answers, broken formulas, misleading Markdown, or unusable progression | Publication workflow distinguishes structural validation from factual, assessment, trust, and preview approval |
| Imported content has a broader trust surface than coding alone | Markdown/rendered resources and browser-evaluated quiz/drill expressions can affect the learner environment before code execution | Authoring and install surfaces state the full trust boundary; unreviewed packs are never described as safe because they contain no coding module |
| Completion and grading states can overstate evidence | Pending or weakly aligned grading can be mistaken for demonstrated competence | Each module declares an observable completion contract; coding without deterministic grading is visibly pending rather than passed |
| Core learning must survive limited devices | Making execution tooling implicit excludes tablet, phone, Chromebook, and low-power users | Every course identifies a non-coding path or explicitly declares its runtime dependency before enrollment; non-coding modules work without optional runtimes |
| Generated courses need a mandatory human review gate | Volume can amplify factual errors, answer leakage, and incoherent sequencing | No course is marked publication-ready without named review coverage and rubric results |

### P1: Coherence, Recovery, and Creator Leverage

| Finding | Desired outcome | Acceptance signal |
|---|---|---|
| Resume context should be more explicit | Returning learners know the next useful action | Usability test participants resume the intended module without inspecting the full catalog |
| Feedback needs a consistent action model | Wrong answers and failed runs teach, not merely score | Every assessment type gives a next action appropriate to its disclosure model; tests preserve delayed answers |
| Creator preview is manual and easy to skip | Course defects are found before sharing | A documented preview matrix covers desktop, narrow browser, all module types used, links/assets, and runtime fallbacks |
| Quality metadata and provenance are informal | Reviewers can understand sources, freshness, and generation scope | Published packs include concise audience/scope, generated-content disclosure, review date, and known limitations |
| Validation feedback should be more actionable | Creators can fix issues without reading parser code | Errors identify track/module/file and expected correction; trust-related warnings are distinguishable from schema errors |
| Accessibility and content readability need explicit gates | Rich content remains usable across input and display modes | Rubric covers heading structure, alt text, contrast-dependent meaning, keyboard use, overflow, and diagram alternatives |

### P2: Ecosystem Learning and Adaptation

| Finding | Desired outcome | Acceptance signal |
|---|---|---|
| Course quality evidence is local and fragmented | Creators can improve a course without surveillance | Opt-in, privacy-preserving export summarizes completion and assessment friction without identity or raw learner content |
| Fork lineage is not a first-class concept | Useful adaptations remain attributable and reviewable | Pack metadata can record upstream source/version and material changes without a central registry |
| Different learners need different pacing | Course forks or modes can support review, standard, and deep paths | A course can describe optional modules or paths without breaking stable core progression |
| Staleness is difficult to see | Time-sensitive courses prompt review before trust decays | Packs can declare review date and freshness-sensitive claims; UI can flag overdue review without blocking local use |
| Quality comparison lacks shared evidence | A future commons rewards maintained courses, not quantity | Any catalog or index uses rubric/provenance/freshness signals and never ranks by engagement alone |

## Phased Roadmap

Phases are ordered by dependency, not calendar promises. A phase exits only when
its acceptance criteria are met.

### First Implementation Wave

Completed on 2026-07-17 as the first response to this plan:

- Learners can pause an enrolled course from `My courses` and later resume it;
  progress, drafts, attempts, and history remain intact.
- Shared course tabs now use the standard automatic-activation keyboard pattern
  with roving focus and linked tab/tabpanel semantics.
- Course validation now checks typed metadata, likely module folders missing
  `module.yaml`, starter files for every declared language, and the structural
  integrity of quiz, test, and drill definitions.
- The creator workflow and publication checklist now cover generation, human
  review, structural validation, learner preview, sharing, and the complete
  trusted-content boundary.

The next implementation wave should close the highest-risk remaining gaps:
constrain authored browser expressions and raw content, make save failures
visible and recoverable, provide a usable mobile coding mode, add non-recording
creator preview, and make pack assets portable without manual copying.

### Phase 0: Baseline and Contracts

- Audit representative reading, coding, quiz, test, and drill modules against
  the rubric below.
- Document current funnel and quality baselines without adding remote telemetry.
- Define course spine, module completion contract, provenance note, review
  record, and trust disclosure templates.
- Confirm that validator, docs, and UI use the same names for module types and
  grading states.

**Exit criteria:** at least one small and one large course have completed audits;
all P0 measures have a baseline or an explicit instrumentation gap; templates
have been used successfully by one creator other than their author.

### Phase 1: Trustworthy Publish Path

- Implement or document checks for required files, metadata, duplicate slugs,
  assessment shape, expression review, local assets, and coding contracts.
- Make trust warnings accurate at install/share decision points.
- Apply generate-review-validate-preview-share to reference courses.
- Ensure course previews expose fit, syllabus, modality, and runtime constraints.

**Exit criteria:** every bundled/reference course passes structural validation,
has no unresolved critical rubric issue, and has a completed publication
checklist; a reviewer can identify all authored behavior before enabling a pack.

### Phase 2: Learner Continuity and Feedback

- Tighten start/resume actions across active courses, previews, modules, and
  stats.
- Standardize recoverable error and next-action language across module types.
- Verify browser-only and narrow viewport flows for non-coding modules.
- Make pending, passed, completed, and attempted states unambiguous.

**Exit criteria:** in moderated tests, at least 4 of 5 participants can enroll,
start, resume, and explain their current completion state without assistance;
all critical learner paths pass keyboard and narrow-viewport checks.

#### AI Tutor

An optional per-module chat with a model served through OpenRouter, available on
every module type.

- **Principle:** primarily 1 (learner agency over engagement) and 5
  (progressive capability); constrained by 10 (claims stay proportional to
  evidence).
- **Priority:** P1, under *Coherence, Recovery, and Creator Leverage*. It exists
  to make a stuck learner's next action plausible, which is the Practice-stage
  evidence in the learner journey.
- **Acceptance criterion:** a learner who fails an attempt can get an actionable
  next step without leaving the module, and the feature adds no required setup,
  no cost, and no degraded path for learners who never enable it. Disabling it
  changes nothing else about the app.
- **Workstream:** learner experience, with trust and security owning the
  third-party boundary.

Deliberate constraints, because this is the one feature that reaches off the
local machine:

- Off by default. No key means the drawer explains setup and nothing else
  changes. It must never become a runtime dependency of a course.
- Solutions and answer keys are withheld from the model by default, so the
  default behavior is hinting rather than answering. Handing over answers on
  demand would undercut *evidence before completion*.
- Tutor output is unverified generated text, like the courses themselves. It
  does not mark modules complete, grant points, or affect progress, and it is
  not presented as authoritative.
- Conversations stay in the local DuckDB file and are scoped per learner and per
  module. The learner can clear a thread.
- The tutor reads the learner's work — editor drafts, run output, grader
  verdicts — through server-side tools rather than the browser uploading it.
  That reach is legible rather than silent: the panel lists what it read while
  answering, and every lookup is scoped to the signed-in learner and the module
  in the URL. A learner who never opens the drawer is never read from.
- Open question: on a shared instance, one key funds every profile's usage with
  no per-profile ceiling. Revisit if shared instances become common.

### Phase 3: Creator Tooling and Evidence

- Produce actionable validation output and a repeatable preview harness.
- Add lightweight provenance, review-date, known-limitations, and lineage
  conventions while preserving ordinary folders.
- Provide local quality summaries that help maintainers find high-friction
  modules without exposing learner drafts or identities.

**Exit criteria:** a new course can move from generated spine to previewed pack
using documented commands alone; maintainers can locate the three highest-
friction modules from local aggregate evidence and trace a pack to its review.

### Phase 4: Responsible Course Commons

- Explore opt-in sharing of packs and non-identifying quality evidence.
- Support fork lineage, freshness review, and optional learning paths.
- Evaluate ecosystem discovery only after trust and quality signals exist.

**Exit criteria:** any shared index is optional, does not become a runtime
dependency, exposes provenance and freshness, and has abuse/reporting and
rollback plans before launch.

## Owners and Workstreams

Owners are durable roles. One person may hold several roles, but each shipped
change needs one directly responsible owner.

| Workstream | Accountable owner | Core responsibilities | Key collaborators |
|---|---|---|---|
| Product philosophy and scope | Product steward | Principles, priority calls, roadmap exits, claim discipline | All owners |
| Learner experience | Learner-experience owner | Discovery, enrollment, navigation, feedback, resume, accessibility | Content, platform, measurement |
| Course authoring and pedagogy | Content-system owner | Spine template, authoring workflow, rubric, examples, reviewer guidance | Subject reviewer, learner experience |
| Content integrity | Subject-matter reviewer | Factual accuracy, source quality, currency, uncertainty, assessment validity | Course creator, safety reviewer |
| Runtime and platform | Platform owner | Parsing, persistence, execution, device fallbacks, performance, validation tooling | Security, learner experience |
| Trust and security | Security owner | Pack threat model, Markdown/browser-expression/runtime boundaries, warning language | Platform, docs |
| Quality and release | Quality owner | Preview matrix, regression coverage, publication checklist, release evidence | Every workstream |
| Measurement and privacy | Measurement owner | Metric definitions, local aggregation, consent, retention, interpretation | Product, security |
| Course maintenance | Named course maintainer | Review dates, issue triage, stable slugs, revisions and changelog | Subject reviewer, learners |

For multi-agent course generation, the lead agent owns the spine and shared
contracts, writer agents own disjoint module ranges, and a separate integrator
owns cross-course coherence. Agents do not self-certify factual correctness or
publication readiness.

## Measurable Acceptance Criteria

These are product-level release gates. Teams may add stricter feature criteria.

### Learner Experience

- A learner can discover, preview, enroll in, start, and later resume a course
  with no app-code or filesystem knowledge.
- In a five-person formative usability round, at least four complete the core
  flow without moderator intervention and can correctly describe what is
  complete versus merely attempted.
- Reading, quiz, test, and drill modules used by a course complete their primary
  interaction at 360 CSS pixels and with keyboard-only input.
- Missing `uv`, `g++`, Docker, or GPU support does not prevent browsing the
  course or completing non-coding modules; affected coding actions name the
  missing capability and a next step.
- Navigation, dynamic feedback, and controls have programmatic labels and do not
  rely on color alone for meaning.

### Course and Assessment Quality

- Every course states audience, prerequisites, outcomes, expected modality, and
  known runtime/device constraints before publication.
- Every stated course outcome maps to at least one module and one observable
  practice or assessment; every scored item maps back to a stated outcome.
- Sampled quiz/test keys, drill formulas, deterministic outputs, and reference
  solutions are independently checked. The sample is 100% for courses with up
  to 50 scored items and at least 30 items plus every high-risk item for larger
  courses.
- All deterministic coding exercises pass from starter-to-solution in every
  declared language and supported mode used for publication testing.
- No critical factual, safety, trust, answer-leakage, broken-navigation, or
  inaccessible-core-flow issue remains open at publication.

### Creator and Sharing Experience

- `npm run course:validate` exits successfully for the publication artifact;
  each warning is fixed or recorded as intentionally accepted.
- A clean checkout or copied folder resolves all local image paths and contains
  every required asset without relying on the creator's machine.
- A second person can follow the documented workflow to validate and preview a
  course without consulting parser source.
- Published packs state source/ref, review date, generated-content involvement,
  known limitations, and whether they include Markdown/raw HTML, parametric
  expressions, starter/reference code, dependencies, or expected outputs.
- Stable track and module slugs are preserved across ordinary updates; breaking
  slug changes are called out because they can disconnect local progress.

### Trust and Privacy

- Trust copy never equates structural validation with safety or accuracy.
- Unreviewed remote content is not enabled silently. The adopter is told that
  rendered content, browser expressions, network-loaded resources, dependencies,
  and learner-run code are relevant review surfaces.
- No success metric requires a cloud account, public profile, raw draft upload,
  or cross-user leaderboard.
- Any future export is opt-in, inspectable before sharing, and excludes code
  drafts, free-form responses, secrets, and direct identity by default.

## Course-Quality Rubric

Score each dimension from 0 to 3 and attach brief evidence.

- **0 - Missing or harmful:** absent, materially wrong, unsafe, or unusable.
- **1 - Present but weak:** substantial correction or redesign is needed.
- **2 - Publication-ready:** clear, correct for scope, usable, and reviewed.
- **3 - Exemplary:** unusually coherent, robust, inclusive, and easy to adapt.

| Dimension | What reviewers inspect |
|---|---|
| Audience and promise | Learner profile, prerequisites, scope boundaries, realistic outcomes, expected effort |
| Structure and progression | Dependency order, pacing, terminology, retrieval/review, difficulty ramp, useful module transitions |
| Explanatory quality | Accuracy, examples, mental models, notation, diagrams, uncertainty, absence of filler and contradiction |
| Practice design | Deliberate practice, varied examples, productive failure, hints that preserve thinking, transfer beyond imitation |
| Assessment validity | Outcome alignment, correct keys/formulas, plausible distractors, no leakage, fair thresholds, appropriate feedback timing |
| Coding contract | Runnable starter, language parity, dependency discipline, deterministic grading when claimed, honest pending states |
| Accessibility and device reach | Headings, alt text, keyboard flow, non-color cues, readable layouts, diagram alternatives, browser-only viability |
| Trust and safety | External links/assets, raw/rendered content, browser expressions, dependencies, execution, domain-specific harm and limitations |
| Portability and maintainability | Valid schema, local assets, stable slugs, concise metadata, review date, provenance, fork-friendly organization |
| Learner experience | Clear start/resume/next action, workload signals, useful feedback, calm progress, coherent completion meaning |

Publication requires:

- No dimension scored 0.
- Audience and promise, explanatory quality, assessment validity, trust and
  safety, and portability and maintainability each score at least 2.
- Total score is at least 20 of 30 for an initial publication.
- Any score of 1 has a named owner, documented limitation, and planned review.
- High-stakes domains require qualified subject and safety review regardless of
  score; this rubric is not a credential.

## Success Metrics

Metrics should diagnose the experience, not become engagement targets. Establish
baselines in Phase 0 and segment by module type, device capability, and course
without exposing individual learners.

### North-Star Evidence

**Outcome-backed progress:** the percentage of enrolled learners who complete at
least one outcome-aligned practice or assessment in a course and later return to
complete another meaningful module. This balances initial value with continuity
without rewarding idle time.

### Learner Measures

- Preview-to-enrollment rate, interpreted with course fit rather than maximized.
- Enrollment-to-first-meaningful-action rate and median time to that action.
- Resume success: return sessions that continue an enrolled course without
  catalog detours or lost drafts.
- Assessment improvement: change between first and best later attempt, separated
  from repeated identical-item memorization.
- Module friction: abandon/error/retry patterns by module and type.
- Browser-only completion rate for non-coding modules.
- Self-reported confidence calibration in periodic opt-in studies, compared with
  assessment evidence rather than used alone.

### Creator and Course Measures

- Time from complete spine to validated preview, excluding subject-review wait.
- Validator errors and warnings per new course, plus time to resolution.
- Publication checklist completion and rubric distribution.
- Defects found after publication by severity and escape category.
- Percentage of published courses with current review date, provenance, named
  maintainer, and no unresolved critical issue.
- Forks or revisions that improve a rubric score, treated as maintenance health
  rather than popularity.

### Guardrails

- No optimization for raw session duration, streak length, points earned, or
  notification-driven return rate.
- Track execution failures, unsafe-content reports, data loss, inaccessible core
  flows, and misleading completion states as release-blocking guardrails.
- Small samples are reported with counts and uncertainty; local-only usage is
  never interpreted as global representativeness.

## Agent-Generated Content Risks

| Risk | Failure mode | Required mitigation |
|---|---|---|
| Confident factual error | Fluent but false explanation or obsolete claim | Qualified human review, source/provenance notes for consequential claims, freshness date |
| Citation laundering | Sources are invented, irrelevant, or do not support the text | Open and verify cited sources; reject unverifiable references; distinguish inference from source claims |
| Incoherent progression | Parallel writers redefine terms, skip prerequisites, or duplicate modules | Lead-owned spine and vocabulary; disjoint ownership; integrator pass across boundaries |
| Assessment leakage | Theory, tips, examples, filenames, or option patterns reveal answers | Separate leakage review; preview in learner mode; inspect randomized variants |
| Invalid assessment logic | Wrong key, unreachable option, biased distractor, unsafe formula, or unstable expected output | Independently recompute keys/formulas; sample generated ranges and edge cases; run declared solutions |
| False determinism | Nondeterministic task is graded by brittle stdout | Use pending verdict or robust contract; document randomness, network, model, and hardware assumptions |
| Unsafe authored behavior | Raw/rendered Markdown, external resources, Mermaid, or browser expressions cause unwanted behavior | Review all authored surfaces; constrain future evaluators; install only trusted packs; do not treat validation as sandboxing |
| Dependency or code supply chain | Starter/reference code or dependencies execute malicious or compromised code | Pin/review dependencies where practical; prefer container modes for isolation; never promise containers eliminate all risk |
| Hidden bias or exclusion | Examples encode stereotypes, assume culture/resources, or create inaccessible tasks | Inclusive review, varied examples, accessible alternatives, explicit prerequisites and equipment needs |
| High-stakes overreach | Course implies medical, legal, financial, safety, or credential authority | Qualified domain review, limitations, escalation guidance, conservative claims; do not publish unsupported advice |
| Fabricated completeness | Large course appears comprehensive but has shallow or missing coverage | Outcome-to-module map, rubric evidence, scope boundaries, representative learner testing |
| Review automation bias | Agent reviews its own output and repeats the same blind spot | Independent reviewer or model plus human adjudication; agents cannot approve their own publication gate |
| Secret or personal data inclusion | Generated examples, logs, drafts, or fixtures expose sensitive data | Use synthetic fixtures; scan assets and history; exclude learner content from shared packs and exports |
| Maintenance decay | Time-sensitive material remains polished but stale | Named maintainer, review date, stale-claim inventory, issue and update path |

## Decision Rules

When priorities conflict, use this order:

1. Prevent material learner harm, data loss, or misleading trust claims.
2. Preserve inspectability, portability, and learner ownership.
3. Protect the integrity of learning and assessment.
4. Keep core study usable across ordinary and browser-only devices.
5. Reduce creator effort without removing meaningful review.
6. Add motivation or ecosystem features only when they do not compromise the
   first five rules.

Revisit this plan when the course schema, trust model, execution model, sharing
model, identity boundary, or success definition changes. Feature delivery alone
is not a reason to rewrite the principles; evidence that a principle or measure
is wrong is.
