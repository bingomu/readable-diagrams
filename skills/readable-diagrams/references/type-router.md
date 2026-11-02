# Type router

Choose by the **shape of the reader's question**, then by grammar. Never pick a
type because it looks impressive.

## 1. Start with the semantic pattern

When behaviour, state, enforcement or risk carries the meaning, name the pattern
first — it survives restyling:

| Trigger in the source | Pattern | Grammar |
| --- | --- | --- |
| fan-in, queue depth, finite capacity, bottleneck | queue / bottleneck | left→right flow, capacity annotated |
| repeated input / rule / output across stages | stage framework | columns with identical slots |
| loose input becomes a structured artifact | raw → structured | left→right with a transform node |
| two rule traces with pass/fail/skip and first divergence | paired traces | two parallel lanes, same x |
| trust boundary plus allowed/forbidden ingress | secure paved road | zones + gated edges |
| controls grouped by where they are enforced | control catalogue | layer stack |
| one subject through phases, waits, retries, terminals | lifecycle | state machine |
| hierarchy where the level carries the claim | traceable decomposition | tree / nested |

## 2. The catalogue

| Reader's question | Type | Engine | Layout guidance |
| --- | --- | --- | --- |
| What is this made of, and what talks to what? | **architecture** | ✅ `architecture` | tiers → columns; zones for trust boundaries; max 9 nodes |
| What are the steps and where do they branch? | **flow** | ✅ `flow` | one direction; decisions are hexagons; short branch labels |
| What states can this be in? | **state machine** | ✅ `state` (graph) | cycles allowed; terminals marked; label transitions |
| In what order do services exchange messages? | **sequence** | ✅ `sequence` | time flows down; return dashed; ≤7 actors |
| When did things happen? | **timeline** | ✅ `timeline` | proportional clock when times are known; ≤3 lanes |
| What contains what? | **tree / nested** | ✅ `tree` | single-parent only; parent centred over children |
| What are the abstraction bands? | **layer stack** | ✅ `layers` | top = highest abstraction; ≤6 bands |
| How do magnitudes compare? | **bar** | ✅ `bar` | start at zero; values printed; one focal bar |
| Where does each option sit on two axes? | **quadrant** | ✅ `quadrant` | name the axes, not the units; one recommended point |
| What changes between two topologies? | **architecture delta** | ✍️ | two synchronised frames + a changes ledger row |
| What is the legacy landscape today? | **IT current-state** | ✍️ | group by department/era; desaturate; label the era |
| Who hands off to whom, cross-functionally? | **swimlane** | ✍️ | lanes = actors, x = time; handoffs are vertical arrows |
| What is the trend over time? | **line / slopegraph / ridgeline** | ✍️ | one axis, labelled ticks; no gridlines unless they carry data |
| How are two variables correlated? | **scatter / bubble / beeswarm** | ✍️ | axis labels + units; annotate 1–2 outliers only |
| What is the distribution in each group? | **box plot** | ✍️ | five-number summary; label the median |
| Where does quantity split and merge? | **sankey** | ✍️ | band width = amount; label nodes, not every band |
| How does one quantity bridge to another? | **waterfall** | ✍️ | signed contributions; start/end totals in ink |
| How does a score profile compare across entities? | **radar / spider** | ✍️ | ≤5 axes, ≤3 series; desaturated series palette |
| What is the cross-tabulated density? | **heatmap** | ✍️ | sequential ramp; value in cell or tooltip-free label |
| What is the part-to-whole composition? | **treemap / marimekko** | ✍️ | area proportional; label cells that fit, legend the rest |
| What is the ranked hierarchy or drop-off? | **pyramid / funnel** | ✍️ | equal steps or proportional; conversion % at each step |
| What overlaps between sets? | **venn** | ✍️ | 2–3 sets max; label intersections |
| What are the causes of one effect? | **fishbone** | ✍️ | 4–6 bones, grouped by category |
| What should we build vs buy and what is moving? | **wardley map** | ✍️ | value chain y, evolution x; movement arrows |
| What is in progress, and where is it blocked? | **kanban** | ✍️ | columns by state; WIP limit in the header |
| What does the customer do vs what the service hides? | **service blueprint** | ✍️ | stages across, line of visibility through |
| What happens across a journey, and how does it feel? | **user journey** | ✍️ | stages across; emotion curve below |
| Where does the software run? | **deployment** | ✍️ | zones / hosts / artifacts; ports as sublabels |
| What depends on what (with cycles)? | **dependency graph** | ✍️ | left→right layers; highlight cycles |
| How is the code structured? | **class / UML** | ✍️ | compartments; only members that matter |
| What is the data model? | **ER / database schema** | ✍️ | table-first: every column, keys as tags |
| How does work break into releases over time? | **story map / Gantt** | ✍️ | x = time; cut line for the release |
| How does a policy evaluate, step by step? | **paired flowchart** | ✅ `flow` ×2 | same x for comparable decisions |

`✅` = render it from a spec. `✍️` = hand-author the SVG following
[`hand-authoring.md`](hand-authoring.md), keeping the same page furniture.

## 3. Choosing between two plausible types

- **Dominant axis wins.** Architecture vs data flow → is the claim about
  structure or about movement? Pick one; the other becomes a caption sentence.
- **Behaviour beats looks.** If the meaning is “what happens when”, draw the
  process/state, not the component map.
- **If a three-column table would teach it, use the table.** Tables are not a
  failure mode; a diagram that should have been a table is.
- **Split before shrinking.** Overview + detail beats a 20-node canvas. Name them
  `<base>-overview.html` and `<base>-<part>.html`.

## 4. Hand-authored layout grammars

Five grammars cover every `✍️` row above. Load the relevant one:

### A. Two-axis plot (line, scatter, bubble, polar, radar)
- Plot area on a 4px grid; axis labels in `eyebrow`, tick values in `sublabel`.
- One y-axis. Two units on one chart is two charts.
- Series colours come from the desaturated palette; the focal series gets
  `accent`. ≤3 series.
- Annotate the 1–2 points the takeaway is about; do not annotate everything.

### B. Sequence of stages (swimlane, journey, blueprint, process)
- x = stages (4–7), y = actors/layers.
- One accent per row at most; the “line of visibility” is a dashed `rule` line.
- Handoffs are the only vertical arrows; horizontal arrows inside a row are
  confidence/collaboration, not data.

### C. Hierarchy (nested, org chart, decomposition, story map)
- Depth ≤4 visible levels; beyond that, collapse to “×N”.
- Parents centre over children; siblings share one axis.
- Containment uses consistent insets (16px per level), not colour alone.

### D. Matrix (kanban, control catalogue, security matrix, heatmap)
- Columns and rows share gutters; header cells are `paper-2` + `eyebrow`.
- Cell fill encodes value on one sequential ramp; text stays `ink`.
- Empty cell ≠ zero: mark “—” explicitly.

### E. Quantity flow (sankey, waterfall, funnel, treemap)
- Width/area is proportional — verify the arithmetic in the caption.
- Label totals at nodes; label the delta, not every slice.
- Round to two significant digits; print units once.

## 5. Multi-panel pages

When the answer needs several figures (e.g. an explainer), the page pattern from
Archify's explainer applies:

1. conclusion paragraph (2–3 sentences, no bullets);
2. one diagram that carries the mechanism;
3. one table or step list for the cases where it does not hold;
4. optional checklist of what the reader must verify.

Each panel answers one question, and every panel after the first supports,
qualifies or applies the conclusion. Stop when nothing is left to support.
