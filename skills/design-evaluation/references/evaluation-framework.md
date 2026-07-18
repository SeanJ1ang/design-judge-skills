# Evaluation Framework

## Score structure

The general score is 100 points:

- design quality: 50 points;
- presentation quality: 50 points.

Maturity changes the design-dimension weights and evidence threshold. It is not itself a scored dimension. Presentation weights remain the same for both tracks.

## Raw-score anchors

| Score | Meaning |
|---:|---|
| 0 | Absent, contradicted, or fundamentally invalid |
| 1 | Severe weakness; a claim exists but basic logic or evidence is absent |
| 2 | Partly established with major gaps or weak evidence |
| 3 | Adequately established but not distinctive or fully evidenced |
| 4 | Strong, clear, and well-supported |
| 5 | Exceptional, comprehensively evidenced, and notably strong for the category |

## Design dimensions

| Key | Dimension | Core question |
|---|---|---|
| `problem_value` | Problem definition and value | Is the problem real, specific, important, and appropriate for design intervention? |
| `user_function_usability` | User value, function, and usability | Does it deliver concrete benefit and credible function, efficiency, safety, comfort, or clarity? |
| `innovation_differentiation` | Innovation and differentiation | Is the difference meaningful, relevant, and supported rather than merely novel-looking? |
| `solution_integrity` | Solution logic and system integrity | Do problem, user, mechanism, workflow, components, and intended outcome form a coherent loop? |
| `implementation_feasibility` | Feasibility and execution evidence | Are technology, structure, materials, manufacturing, cost, maintenance, service, or implementation credible? |
| `form_interaction_quality` | Form and interaction quality | Do form, proportion, CMF, ergonomics, interface, and interaction support function and experience? |
| `responsibility_sustainability` | Social, ethical, and sustainability responsibility | Are environmental, inclusive, safety, fairness, ethical, and long-term effects built into the proposal? |

## Presentation dimensions

| Key | Dimension | Core question |
|---|---|---|
| `first_glance_message` | Core message and first-glance recognition | Can the project type, value, and main idea be understood quickly? |
| `information_hierarchy` | Information hierarchy and reading path | Is the problem-to-solution narrative ordered and legible? |
| `function_flow_visualization` | Function, flow, and interaction visualization | Do the materials show how it is used, how it works, and what changes? |
| `scenario_narrative` | Use scenario and user narrative | Are user, context, pain point, and intervention concrete and credible? |
| `detail_evidence_presentation` | Detail evidence and credibility presentation | Are structure, dimensions, materials, prototypes, states, tests, or system links visible? |
| `visual_consistency` | Visual consistency and production finish | Are rendering, photography, graphics, layout, and text coherent and professional? |

## Evidence caps

Evidence caps make unsupported high scores auditable. Apply the cap before weighting.

- Any dimension with `Supported` evidence cannot exceed 4/5; a 5 requires direct `Verified` evidence.
- Any dimension with only `Claimed` evidence cannot exceed 2/5.
- For either maturity track, `implementation_feasibility` with `Claimed` or `Missing` evidence cannot exceed 2/5.
- For Mature Work, `implementation_feasibility` with only `Supported` evidence cannot exceed 4/5; a 5 requires `Verified` implementation evidence.
- Any dimension with `Missing` evidence cannot exceed 1/5 unless the score represents an explicitly observed contradiction.
- A safety-critical or harm-critical claim without validation becomes a Critical finding; do not hide it inside a numeric deduction.

Do not cap other dimensions merely because the supplied presentation is brief. State the material limitation and use the most defensible score.

## Confidence

Evidence confidence is calculated separately:

- `High`: substantial weighted evidence is Verified, the remaining core evidence is Supported, and no core dimension is Missing;
- `Medium`: the core logic is assessable but several claims remain unverified;
- `Low`: major conclusions depend on claims, inaccessible materials, or missing evidence.

Confidence changes how firmly conclusions are stated. It is not a hidden score multiplier.

## Finding severity

| Severity | Definition |
|---|---|
| Critical | Invalidates a core claim, creates serious harm risk, or makes the design fundamentally unreliable |
| Major | Materially weakens function, value, differentiation, feasibility, responsibility, or comprehension |
| Minor | Local weakness with limited impact on the overall proposal |

## Competitiveness labels

| Score | Base label |
|---:|---|
| 85–100 | Strong competitiveness |
| 70–84.99 | Competitive with gaps |
| 55–69.99 | Developing |
| 0–54.99 | Weak or insufficiently evidenced |

When at least one Critical finding is unresolved, replace the base label with `Critical risk` while retaining the numeric score for diagnostic transparency.
