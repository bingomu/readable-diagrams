# The comprehension contract

A diagram is not finished when everything is added. It is finished when a reader
who was not in the conversation can answer the question the figure was drawn for
— without asking you.

This file is the long form of SKILL.md §4. It covers what the machine gate cannot
judge: wording, ordering, and what to leave out.

---

## 1. Start from the reader's question

Write the question in one line before choosing a type:

> 读者看完这张图，要能回答：**「一次下单请求到底经过哪些服务，慢在哪一跳？」**

If you cannot write that question, you are about to draw decoration.

Then name the reader. Vocabulary follows the reader, not the source:

| Audience | Node names | Sublabels | Edge labels | Never |
| --- | --- | --- | --- | --- |
| `engineer` | exact component names | ports, protocols, versions | `POST /v2/orders`, `SQL` | vague verbs like “connects to” |
| `mixed` | component names, acronyms expanded | technology only where it changes a decision | plain verbs — 校验、写入、通知 | ports, versions, codenames |
| `executive` | capabilities and outcomes | none | business verbs — 审批、扣款、通知 | vendor names, infrastructure |

Two rules hold at every level: **never invent detail to fill a slot**, and **keep
the source's proper nouns** (renaming `Kafka` to “消息总线” is fine; renaming it
to another product is a factual error).

---

## 2. The title states the conclusion

The title is read more often than the figure. Make it carry a claim.

| Weak (category) | Strong (conclusion) |
| --- | --- |
| 订单系统架构图 | 一次下单请求如何穿过网关到达数据库 |
| Payment flow | 支付失败时钱会退回，但到账要等 3 天 |
| Q4 路线图 | Q4 只做两件事：降延迟、补导出 |
| Org chart | 值班链只有两级，升级到谁一目了然 |

Rules:

- ≤60 characters, no trailing colon, no “示意图/architecture diagram”.
- Name the mechanism or the consequence, not the file type.
- One claim. If the title needs “和”, the figure is two figures.
- Same nouns in title, labels, caption and steps. A reader matches words, not shapes.

---

## 3. One takeaway sentence

Directly under the title, one sentence that a reader could repeat to a colleague.

- It is a **claim with a direction**: “P99 涨到 600ms，而 P50 没动” — not “展示了延迟数据”.
- It may contain a number, but the number must also exist in the figure.
- 8–100 characters. Longer means you are explaining; move the explanation to the caption.

---

## 4. The caption teaches reading order

The caption is not an alt text and not a restatement. It answers:

1. **Direction** — “从左往右是请求方向”, “从上往下是时间”.
2. **Encoding** — “实线同步，虚线异步”, “橙色是建议先做的一项”.
3. **Provenance** — “示意结构，非实测”, “数据来自 10-31 压测”.
4. **Omission** — “省略了鉴权与日志，它们不改变结论”.

12–80 characters is the useful band. If the caption repeats the takeaway, cut it.

---

## 5. Reading path: 2–5 numbered stops

A reader needs an entry point. Without one they start at the largest box and
wander.

- Pick the stops that **answer the question**: entry → turning point → outcome.
- 2–5 stops. More than five is a process list, not a reading path.
- The number on the figure and the step list below must match; the checker counts
  the list, so keep them equal.
- Steps are named with the same words as the nodes they point at.
- Charts (bar, quadrant, timeline) get steps too: “先看最长的一根” is a legitimate
  first stop.

In the spec: `meta.reading_path` (node ids, titles auto-filled) or `meta.steps`
(`[{title, detail}]` when you want custom wording).

---

## 6. The one-question rule

Each figure answers exactly one question. Symptoms that you have two figures:

- The title needs “和/以及/plus”.
- Two disconnected clusters with no edge between them.
- The legend has two focal colours doing different jobs.
- You catch yourself writing “另一方面……” in the caption.

Split into `<base>-overview.html` + `<base>-<part>.html`, link them in the reply.

---

## 7. Density and deletion

Target density: **4/10** — technically complete, still scannable.

Run the remove test before rendering:

- Can I remove a node? Would the reader still get the answer? → remove it.
- Can I merge two nodes? Do they always travel together? → merge.
- Can I remove an arrow? Is the relationship obvious from layout? → remove.
- Can I remove a label? Does shape/position already say it? → remove.

Budgets the gate enforces: ≤9 nodes for architecture / flow / state, ≤7 actors for
sequence, ≤14 for tree, ≤12 for timeline / bar, ≤10 for quadrant, ≤6 for layers.
Over budget is not a styling problem; it is a “split the diagram” signal.

---

## 8. Label writing

| Slot | Rule | Example |
| --- | --- | --- |
| Node name | noun or short verb phrase, ≤10 CJK chars / 4 EN words | 订单服务, 回滚开始 |
| Sublabel | technical value only (port, type, unit) | `:443`, `PostgreSQL`, `ms` |
| Edge label | what the receiver does, ≤6 CJK / 3 EN words | 校验、写入、超时重试 |
| Branch label | the answer to the decision, 1–4 chars | 是 / 否 / 超时 / 余额不足 |
| Step title | the node it points at, verbatim | 抓慢请求 trace |

Avoid: “连接到”, “调用关系”, “数据流”, “相关”, “处理” — these say nothing. If an
edge genuinely has no interesting label, leave it blank rather than filling it
with a non-word; the checker allows up to 40% unlabelled edges.

---

## 9. Colour and focal budget

- `accent` marks **the thing the title is about** — 1–2 elements, never more.
- Everything else is `ink` / `muted` / `soft`. Hierarchy comes from position,
  border weight and grouping, not from hue.
- Colour is never the only carrier of meaning: pair it with shape, position,
  label, or line style.
- In the light theme the accent is darkened to clear 4.5:1; do not substitute the
  raw brand colour on paper.

---

## 10. Anti-patterns (each one has shipped in real decks)

| Anti-pattern | Why it fails | Instead |
| --- | --- | --- |
| Title is the category (“架构图”) | reader learns nothing before the figure | state the mechanism or consequence |
| Every node identical | erases hierarchy | vary fill/border by role; zone by tier |
| 3 equal summary cards | generic grid, no reading order | vary widths; use the step list |
| Coral/accent on 5 nodes | the signal disappears | 1–2 focal elements |
| Legend floating inside the plot | collides with marks | legend strip below the figure |
| Arrow label sitting on its stroke | the line becomes untraceable | mask + 6–10px gap |
| Diagonal connectors | unreadable at a glance | right-angle elbows |
| Vertical `writing-mode` labels | unreadable | rotate the layout, not the text |
| Dense 20-node single canvas | wiring diagram, not a schematic | overview + detail |
| Restating the figure in the caption | wasted attention | teach direction/units/omission |

---

## 11. Which gate catches what

| Rule | `comprehension_check.py` | `self_check.py` |
| --- | --- | --- |
| Conclusion title ≤60 | ✅ FAIL/WARN | — |
| Takeaway present | ✅ FAIL | — |
| Caption present | ✅ FAIL | — |
| Numbered reading path | ✅ FAIL for structural types | — |
| Legend coverage | ✅ FAIL when kinds/variants exist | — |
| Focal accent ≤2 | ✅ FAIL | — |
| Node budget | ✅ FAIL | — |
| Edge label coverage | ✅ WARN below 60% | — |
| Type-size floors | ✅ WARN | — |
| Token contrast | ✅ FAIL below 4.5:1 | — |
| Orthogonal connectors | ✅ WARN | — |
| Accessible SVG | — | ✅ FAIL |
| Content inside viewBox | — | ✅ FAIL |
| Single-file safety | — | ✅ FAIL |

The remaining rules — one question per figure, captions that teach, no invented
detail — are the author's job. The gate narrows the failure surface; it does not
replace reading your own figure once before sending it.

---

## 12. Final pass (30 seconds, before delivery)

- [ ] Read only the title + takeaway: do they answer the question?
- [ ] Read only the numbered steps: is the story in order?
- [ ] Squint: is the focal element obvious without reading labels?
- [ ] Read every edge label aloud: any non-word left?
- [ ] Check the caption: direction, units, provenance, omission?
- [ ] Would a table have been better? (If yes, say so and offer one.)
