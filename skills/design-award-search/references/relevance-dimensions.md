# Relevance Dimensions

Use the canonical category as a mandatory gate. Search and rank candidates separately across the eight dimensions below. Do not collapse them into one weighted similarity score.

## 1. Problem and user

Match the underlying need, condition, underserved group, or user population.

Evidence examples: addiction recovery, anxiety management, older adults, clinicians, home caregivers.

## 2. Core function

Match the primary job performed or outcome produced.

Evidence examples: detect stress, warn of risk, support rehabilitation, prevent relapse, monitor adherence.

## 3. Sensing technology

Match how the design captures or infers state.

Evidence examples: ECG, HRV, EDA, pressure sensing, computer vision, acoustic sensing, biosignal algorithms.

## 4. Intervention mechanism

Match how the design changes behavior or condition after sensing or user input.

Evidence examples: haptic guidance, paced breathing, biofeedback, neurostimulation, light prompts, medication reminders.

## 5. Physical form

Match product type, body location, attachment method, scale, portability, or wear mode.

Evidence examples: adhesive chest patch, wrist wearable, ring, vest, handheld medical device.

## 6. Use context and workflow

Match where, when, and within which user or clinical workflow the design operates.

Evidence examples: daily out-of-clinic use, emergency response, home rehabilitation, continuous monitoring, high-risk moments.

## 7. System architecture

Match the components and information flow that form the complete experience.

Evidence examples: sensor plus app, device-cloud-clinician loop, hardware with personalized analytics, disposable patch plus reusable module.

## 8. Visual language

Match visible design attributes rather than function alone.

Evidence examples: silhouette, proportion, color and material, surface treatment, medical friendliness, discretion, softness, or low-stigma appearance.

Require a user image and accessible official project images for a `High` or `Medium` visual-language match. Inspect both pixel sets directly and record at least two paired observable attributes. Do not infer visual similarity from project titles, text descriptions, or search snippets alone. Do not persist, embed, or redistribute official images; a marked session-scoped review file is allowed only when a local-path visual tool requires it and must be cleaned in the same task.

## Evidence assignment

- Assign exactly one `Primary relation` to every result: the dimension with the clearest official evidence.
- Assign no more than two `Secondary relations` when evidence is explicit.
- Keep the result once when it matches several dimensions; do not repeat it under multiple groups.
- Keep visual-language and physical-form separate: physical form concerns product configuration and wear mode; visual language concerns visible expression and CMF.
- A candidate that matches only visually must still pass the same or adjacent canonical-category gate.
