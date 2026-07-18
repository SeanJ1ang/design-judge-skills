# Functional Design Category Taxonomy

## Classification rule

Classify in this order:

1. Primary function: the job performed or problem solved.
2. Designed object or service: what the user directly interacts with.
3. Use context: home, hospital, workplace, mobility, public space, or digital environment.
4. Target user: consumer, professional, child, older adult, disabled user, or institution.
5. Technology, material, and appearance: use only as tie-breakers.

Choose one primary category. Add at most two adjacent categories for query expansion. Do not classify by visual resemblance alone.

## Canonical categories

| Canonical category | Typical functions and objects | Adjacent terms |
|---|---|---|
| Medical and Health | diagnosis, treatment, rehabilitation, monitoring, medication, clinical devices | healthcare, wellness, rehabilitation, patient care |
| Accessibility and Inclusive Design | assistive products, sensory access, mobility assistance, independent living | universal design, disability, elderly care |
| Consumer Technology | personal electronics, smart devices, audio, imaging, connected products | electronics, smart product, digital device |
| Home and Kitchen | cooking, cleaning, storage, domestic appliances, household care | household, domestic appliance, kitchenware |
| Furniture | seating, tables, storage furniture, workplace or residential furniture | interior product, furnishing |
| Lighting | task, ambient, architectural, portable, and outdoor lighting | luminaire, lamp, illumination |
| Mobility and Transportation | vehicles, micromobility, transit, navigation, mobility systems | automotive, transport, bicycle, public transit |
| Commercial and Industrial | tools, machinery, manufacturing, logistics, professional equipment | industrial equipment, B2B product, engineering tool |
| Office and Productivity | workplace tools, collaboration hardware, stationery, productivity systems | office equipment, work tool |
| Digital Interaction | applications, interfaces, digital platforms, interactive systems | UX, UI, software, digital product |
| Service Design | end-to-end services, customer journeys, public services, service systems | experience design, system design |
| Communication and Branding | identity, campaigns, information design, wayfinding, editorial systems | graphic design, visual communication |
| Packaging | product containment, protection, dispensing, transport, retail presentation | package, container, sustainable packaging |
| Children and Education | learning tools, toys, school products, child development | educational product, learning, play |
| Sports and Outdoor | training, fitness, recreation, camping, outdoor safety | sporting goods, exercise, outdoor equipment |
| Lifestyle and Personal Accessories | wearables, personal care, fashion accessories, travel goods | lifestyle product, personal product |
| Environment and Spatial Design | interiors, exhibitions, public spaces, architecture, spatial systems | environment, interior, installation, spatial experience |
| Social Impact | community welfare, humanitarian response, public benefit, underserved users | social design, community, public interest |
| Sustainability and Circular Design | reuse, repair, low-impact systems, resource recovery, circular products | eco-design, circular economy, sustainable product |
| Concept and Speculative Design | future scenarios, non-commercial concepts, exploratory proposals | design concept, speculative, experimental |

## Ambiguity rules

- Classify a rehabilitation device as `Medical and Health`; add `Accessibility and Inclusive Design` only when independence or disability access is central.
- Classify a health application as `Digital Interaction`; add `Medical and Health` when the function is clinical or health-specific.
- Classify sustainable packaging as `Packaging`; add `Sustainability and Circular Design` as an adjacent category.
- Classify an educational toy as `Children and Education`; add `Lifestyle` only when learning is secondary.
- Classify a mobility aid by its primary job: use `Accessibility and Inclusive Design` for personal assistance and `Mobility and Transportation` for transport systems.
- When object and function imply different categories, let the primary user job control the primary category.

## Query profile format

```yaml
object: home rehabilitation trainer
primary_function: support upper-limb motor rehabilitation
target_user: adults recovering from stroke
use_context: home rehabilitation
canonical_category: Medical and Health
adjacent_categories:
  - Accessibility and Inclusive Design
english_terms:
  - upper limb rehabilitation
  - home therapy device
  - stroke recovery training
```
