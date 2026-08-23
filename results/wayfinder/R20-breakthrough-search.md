# รายงาน: ทางที่เหลือสำหรับยกระดับ hidden score ARC-AGI-3

## 1. Verdict (บรรทัดเดียว)

หลักฐานที่รอดทั้ง 22 ชิ้นมี **candidate ที่คุ้มสร้างจริง** และตรงกับอาการที่วัดเอง (plateau ที่มี budget เหลือ, search/sim แค่ 2% ของ turn) แต่ **ไม่มีแหล่งไหนพิสูจน์ว่าจะพา hidden ไปถึง 3.00 บนโมเดล 27B ของเราเอง** — หลักฐานที่แน่นที่สุด (Symbolica 4.52 levels/game, arc-skill RHAE 100) วัดบน Claude Opus 4.6/5 ปิดและใหญ่กว่าเรามาก ไม่มีใครวัด mechanism เดียวกันบนโมเดล 27B open-weight ระดับเรา ความหวังมีจริงแต่ยังไม่พิสูจน์ที่ scale ที่เราใช้งานอยู่

---

## 2. Ranked candidates

| # | Candidate | เปลี่ยนอะไร | ผลคาดต่อ LEVELS CLEARED | Cost to build | Source |
|---|---|---|---|---|---|
| 1 | **Mandatory falsifiable prediction gate** — บังคับ agent เขียน typed prediction (cell/move/region/vanish/level/change/noop) ก่อน action ทุกครั้ง, harness diff เทียบ frame จริงแล้วเก็บ HIT/MISS + REFUTED list | ตรงเป้าที่สุดกับ gap ของเรา (search/sim 2% ของ turn) — evidence เดียวกันโชว์ miss rate ตกจาก 37.1%→2.9% เมื่อบังคับ predict ก่อน act; รันจริงถึง RHAE 100 (25/25 เกม) | เพิ่มโดยตรงจาก action ที่รู้ผลก่อนยิง ไม่ใช่ action มั่ว | **ต่ำ** — schema+diff function ใน harness เดิม, 0 model call เพิ่ม, ไม่ต้อง train | https://github.com/pbshgthm/arc-skill |
| 2 | **Stagnation-triggered Refiner** — ทริกเมื่อ N action ไม่มี state change, เรียก call แยกอ่าน raw trajectory แล้ว rewrite memory/skills scratch-file ต่อ (ไม่ restart episode) | ตรงเป้ากับ "top games plateau มี budget เหลือ" ตรงตัว | **ต่ำ-กลาง** — 1 extra call แบบมีเงื่อนไข + 2 scratch-file | https://sethkarten.substack.com/p/continual-harness-an-efficient-self |
| 3 | **Dead-signature blacklist** — จำ (object-color, shape, action) ที่เคยกดแล้ว frame ไม่เปลี่ยน แล้วซ่อน/แจ้งเตือนไม่ให้ agent เลือกซ้ำ | ลด action ที่เสียไปกับสิ่งที่พิสูจน์แล้วว่าตาย — ตรงกับ pattern "24-47 action ต่อ level ที่ fail" | **ต่ำมาก** — dict-lookup ล้วน ไม่มี model call | https://arcprize.org/blog/arc-prize-2026-milestone-1 |
| 4 | **State-graph shortest-path-to-frontier hint** — เก็บ graph ของ (perceptual-hash frame → action → next-hash) แล้ว inject hint ว่า action ไหนยังไม่เคยลอง+ใกล้สุด | ablation จริง: 19/30 เทียบ 5/30 ของ LLM+DSL baseline บน budget เท่ากัน — ตอบโจทย์ที่เราปิด direction #7 (learned model ไม่มี coverage) ด้วยของถูกกว่า | **กลาง** — ต้องคำนวณ shortest-path ทุก turn แต่ไม่ต้อง train | https://arxiv.org/html/2512.24156 |
| 5 | **Executable world-model + simulate-before-commit** — ให้ agent maintain state.py/transitions.py/planner.py ใน sandbox ที่มีอยู่แล้ว, บังคับ verify แผนกับ history จริงก่อนยิง action จริง | 106/209 levels, mean RHAE 32.58% — evidence รองจาก #1 แต่ mechanism ครอบคลุมกว่า | **กลาง-สูง** — ต้อง discipline การเขียน/refactor 3 ไฟล์ ไม่ใช่แค่ schema | https://arxiv.org/html/2605.05138v2 |
| 6 | **Per-game persistent skills library** — เขียน executable macro ที่ confirm แล้วลงไฟล์คงอยู่ข้าม level ในเกมเดียวกัน re-inject ทุก level ถัดไป | Voyager: 3.3x unique item บน budget เดียวกัน; Continual Harness: 62% ของ action ที่รันจริงมาจาก skill reuse ไม่ใช่ reasoning สด | **ต่ำ-กลาง** — ไฟล์ต่อเกม + system-prompt injection | https://arxiv.org/abs/2305.16291 , https://sethkarten.substack.com/p/continual-harness-an-efficient-self |
| 7 | **Perception self-check (grid-read audit)** — dump ค่าที่ model "อ่าน" จาก 5 turn เทียบ ground-truth array ใน sandbox; ถ้า mismatch สูง ให้ลอง ASCII-only / patch-aligned PNG (32px/cell) / ลด color count | evidence เฉพาะ Qwen family: Qwen3-VL-8B (สาย lineage เดียวกับโมเดลเรา) exact-match = 0% ตั้งแต่ 4x4; text-encoding ชนะ image-encoding 20-55 F1 จุด ข้าม 3 ค่าย model | **ต่ำมาก** — แค่ log+diff ที่มีข้อมูลอยู่แล้วใน sandbox, ครึ่งวัน | https://arxiv.org/html/2604.09687 , https://arxiv.org/html/2602.15950v2 , https://arxiv.org/html/2503.23064v2 |
| 8 | **Online "will this action change anything" classifier** — MLP/logistic เล็ก ๆ train สดต่อเกมจาก (action, frame-changed?) ที่เก็บมาแล้ว, ใช้ re-rank action ที่จะเสนอให้โมเดล | mechanism ของ StochasticGoose (ผู้ชนะ preview) ที่แก้ปัญหา "350 move แรกกดมั่ว" | **กลาง** — train loop เล็กในตัวเกม ไม่ใช้ internet/pretrained | https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings |
| 9 | **Action-space reduction ด้วย connected-component grouping** — ก่อนส่งภาพให้โมเดล group cell สีเดียวกันติดกันเป็น shape object แล้วเสนอ shape เป็น click candidate แทน pixel | ลด action space ~100x ตามที่ 2nd-place agent ทำ | **ต่ำ** — scipy.ndimage.label ล้วน ไม่ ML | https://github.com/wd13ca/ARC-AGI-3-Agents |
| 10 | **Mandatory EXPLORE-before-commit phase gate** — K action แรกหลัง level เปลี่ยน (หรือหลัง stagnation) ต้องลอง action ที่ผลไม่รู้ก่อนอนุญาต action ที่ "รู้ผลแล้ว" | RHAE 0→0.2116 บน Qwen2.5-0.5B (เล็กกว่าเรามาก) จาก explore-gate เพียงอย่างเดียว — ทิศถูกแต่ effect size เล็ก เพราะโมเดลอ่อนกว่าเรามาก | **ต่ำ** — state-machine รอบ turn loop เดิม | https://arxiv.org/abs/2605.25931 |
| 11 | **Sandbox candidate-sequence drafting + frame-diff selection (k-of-n)** — เมื่อ stagnate ให้ draft k แผนสั้น ๆ ใน sandbox, ยิงตัวที่มั่นใจสุด, ใช้ frame-diff จริงเป็น verifier เลือกต่อ | coverage scale แบบ log-linear ตาม N — ใช้ได้เพราะเรามี verifier ฟรีอยู่แล้ว (frame diff) ไม่ต้อง train reward model | **กลาง** — ผูกกับ #1 (ต้องมี prediction infra ก่อนถึงจะ diff ได้คุ้ม) | https://arxiv.org/abs/2407.21787 |
| 12 | **Concurrency reduction A/B (25→12-15 เกม)** | throughput/latency tradeoff ที่วัดจริงบน local serving — ปลดปล่อย token/sec ต่อเกมให้ deliberation มากขึ้น "ฟรี" โดยใช้ GPU เดิม | **UNVERIFIED สำหรับเรา** — เป็นแค่ config sweep ไม่ใช่ mechanism ที่พิสูจน์ว่าแก้ depth | **ต่ำมาก** — เปลี่ยน concurrency param อย่างเดียว | https://jangwook.net/en/blog/en/local-llm-concurrent-requests-num-parallel-experiment/ |
| 13 | **Budget forcing ("Wait" forced continuation) ที่จุด stagnation** | AIME24 +7 จุดจาก inference-time เพิ่ม โดยไม่ train เพิ่ม — ตรงกับ "top games หยุดคิดเร็วทั้งที่มี wall-clock เหลือ" | **UNVERIFIED**: วัดบน Qwen2.5-32B ที่ผ่าน reasoning-SFT แบบเฉพาะ — ไม่รู้ว่า checkpoint ของเรามี "thinking phase" ที่ตอบสนองแบบนี้ไหม | **ต่ำมาก** — 1 บรรทัด inject ก่อน tool call | https://arxiv.org/abs/2501.19393 |
| 14 | **Selective test-time compute allocation (design principle เท่านั้น)** — ไม่ต้อง RL train เอง แต่ใช้ stagnation heuristic เดียวกับ #2/#10/#13 เป็น trigger | อธิบายว่าทำไม throughput เพิ่มเฉย ๆ (direction #3 ที่เราปิดแล้ว) ไม่ช่วย — ยืนยัน design ของ candidate อื่นในตารางนี้ ไม่ใช่ item ที่ build เอง | N/A — ใช้เป็น rationale | https://arxiv.org/abs/2509.03581 |
| 15 | ~~Speculative decoding~~ — **อย่าลงทุน** | speedup หดเมื่อ batch ใหญ่ (compute-bound) ตรงกับที่เราวิ่ง 25 agent concurrent อยู่แล้ว, ยิ่งไปกันได้กับ closed item #3 ที่ throughput ไม่แปลงเป็น depth | N/A — skip guidance | | https://specdecode-bench.github.io/ |
| 16 | Symbolica orchestrator/subagent delegation (Arcgentica) — ceiling สูงสุดในตาราง (4.52 levels/game) | มี evidence ตัวเลขแรงสุด แต่วัดบน Claude Opus 4.6 120k context ปิด ไม่มีอะไรยืนยันว่า mechanism เดียวกันจะรอดบนโมเดล 27B ของเรา | **สูง** — ต้องเพิ่ม subagent-spawn tool schema + summarization step ที่กิน compute เอง | https://www.symbolica.ai/blog/arc-agi-3 |
| 17 | Symbolica cost-vs-capability comparison (harness ชนะ compute 144x) | หลักฐานสนับสนุนทิศทาง "harness > compute" — ไม่ใช่ item ที่ build เอง เป็น rationale สำหรับตารางทั้งใบ | N/A | https://www.symbolica.ai/blog/arc-agi-3 |
| 18 | AERA benchmark critique — 25 public เกมส่วนใหญ่ solvable ด้วย trivial heuristic, hidden set (110 เกม) เท่านั้นที่วัด intelligence จริง | เป็นคำเตือนต่อ validation methodology ไม่ใช่ mechanism เพิ่ม level — ใช้คัดว่า local A/B ไหนเชื่อได้ | N/A — ไม่มีโค้ดต้อง build | https://arxiv.org/abs/2605.25931 |

---

## 3. สิ่งที่จะสร้างต่อไป — และทำไมชนะตัวรองแชมป์

**สร้าง #1 (mandatory prediction gate) เป็นอันดับแรก** ไม่ใช่ #7 (perception self-check) แม้ #7 ถูกจนต้องเช็ค "ก่อนแตะอะไรอย่างอื่น" ตามคำแนะนำในแหล่งของมันเอง เหตุผล:

**#1 self-diagnose #7 ให้ฟรี.** ถ้าโมเดลอ่าน grid ผิด (ซึ่งมี evidence เฉพาะ Qwen family ว่าเป็นไปได้จริง) มันจะทำนาย prediction ผิดแม้กับ claim ง่าย ๆ (เช่น "เซลล์ X,Y จะเปลี่ยนสี") — miss rate ที่สูงผิดปกติบน prediction ง่าย ๆ **คือ**หลักฐาน perception collapse ที่ #7 ต้องการวัดอยู่แล้ว ไม่ต้องแยกสร้าง diagnostic คนละตัว

**#1 คือ primitive ที่ #2 กับ #3 ต้องใช้ต่อ.** REFUTED list ที่ #1 สร้างจาก MISS = dead-signature ของ #3 พอดี (action ที่ predict ผิดซ้ำ ๆ = action ที่ไม่มีผล) และ confirmed-fact memory ที่ Refiner (#2) ต้องอ่านตอน stagnation ก็คือ HIT list ของ #1 นั่นเอง — สร้าง #1 ตัวเดียวได้ประโยชน์ของ #2/#3 มาเกือบฟรี ต่างจาก #16 (Symbolica) ที่ต้องเพิ่ม subsystem ใหม่ทั้งก้อน (subagent spawn + summarization) โดยไม่มีหลักฐานว่ารอดที่ 27B

**Evidence ของ #1 เป็นตัวเลขเดียวในตารางที่แยก "ก่อน/หลัง" ชัดที่สุด** (miss rate 37.1%→2.9% เมื่อบังคับ predict) — ไม่ใช่แค่ aggregate score ที่บอกไม่ได้ว่ามาจากไหน เหมือนตัวเลขอื่นส่วนใหญ่ในตาราง

**Cost ต่ำสุดในกลุ่มที่มี evidence แรง** — ไม่ต้อง train, ไม่ต้อง internet, ไม่เพิ่ม model call ต่อ turn, ใช้ Qwen3.8-27B-FP8 ปัจจุบันได้ทันทีเพราะเป็น discipline gate (บังคับ format) ไม่ใช่ capability gate (ต้องการความฉลาดเพิ่ม)

**ตัวรองแชมป์ #3 (dead-signature)** ถูกกว่าจริง แต่แคบกว่า — หยุดแค่การกดซ้ำสิ่งที่ "รู้แล้วว่าตาย" ไม่บังคับให้ agent ตั้งสมมติฐานก่อนกด action ใหม่เลย ส่วน #2 (Refiner) เจาะ symptom ตรงกว่าแต่ยังไม่มีกลไกตัดสินว่าอะไรคือ "fact ที่ยืนยันแล้ว" — #1 ตอบคำถามนั้นให้ทั้งคู่โดยไม่ต้องออกแบบเพิ่ม

---

## 4. REFUTED

| Claim | ทำไมตก (เลนส์) |
|---|---|
| Prime Intellect "Prime Agent" (RLM) เคลียร์ครบ 183/183 level, RHAE 95.0-95.5% | **Provenance lens**: เป็น vendor product ปิด self-report เอง ไม่ยืนยันว่าวัดบน Kaggle hidden set หรือ eval track เดียวกับเรา ไม่มี open-weight model ที่รันได้ในข้อจำกัดของเรา (single GPU, no internet) |
| (เคสเดียวกัน) | **Metric lens**: RHAE เป็น efficiency-relative metric ไม่ใช่ raw levels-cleared count — ตัวเลข self-report บน track ที่ไม่ยืนยัน ไม่พอจะนับเป็น depth lever ได้จริง |

---

## 5. สิ่งที่การค้นหาตอบไม่ได้

- **Transfer gap ตัวใหญ่สุด**: หลักฐานที่แรงสุดทั้งหมด (Symbolica 4.52 levels/game, arc-skill RHAE 100/miss 2.9%) วัดบน **Claude Opus 4.6/5** (120k context, closed) ไม่มีใครวัด mechanism เดียวกันบนโมเดล open-weight ระดับ 27B แบบเรา — ไม่รู้ว่า prediction-gate จะให้ miss-rate delta ขนาดเดียวกันไหมเมื่อโมเดลอ่อนกว่ามาก
- **Qwen3.8-27B-FP8 มี interruptible "thinking phase" ไหม** — budget forcing (#13) พิสูจน์บน reasoning-SFT 32B เท่านั้น ไม่รู้ว่า checkpoint ของเราตอบสนองแบบเดียวกัน
- **25 เกม public ของเราซ้อนกับ "trivially solvable" pool ของ AERA แค่ไหน** — ไม่มีใครนับว่าเกมที่เรา plateau อยู่ตรงกับ single-step/probe-solvable ตามที่ AERA จัด class หรือไม่ ถ้าใช่ ผลจาก local A/B อาจไม่ transfer ไป hidden set เลย
- **hidden 110 เกมมีโครงสร้างยังไง** — ไม่มีแหล่งไหนบอกว่า level ในเกม hidden reuse mechanic กันเหมือนที่ ARC-AGI-3 technical report อ้างทั่วไปหรือเปล่า ถ้าไม่ reuse per-game skill library (#6) จะไม่ได้ประโยชน์
- **bottleneck จริงของเราคืออะไรกันแน่** — ไม่มี source ไหน (และเราเองก็ยังไม่วัด) แยกว่า plateau มาจาก exploration strategy, perception misread, หรือ genuine reasoning depth shortfall — candidate ทั้งหมดเป็น mechanism ที่ "อาจช่วย" ไม่ใช่คำตอบว่า mechanism ไหนตรงกับ root cause ของเราที่สุด
- **vLLM serving รองรับ structured prediction schema แบบ #1 โดยไม่เพิ่ม latency ต่อ turn ไหม** — ไม่มีใครวัด overhead ของ mandatory tool-schema field บน stack ปัจจุบันของเรา (Qwen3.8-27B-FP8, 25 concurrent)
---

# ภาคผนวก — การอ่าน verdict ใหม่ (เขียนโดย L0 หลังรับ report)

## quorum ที่ผมตั้งไว้ผิดโครงสร้าง

Workflow นี้ใช้ 3 lens ที่ถาม **คนละคำถาม** (`exists` แหล่งพูดแบบนั้นจริงไหม · `applies` รอดข้อจำกัดเราไหม · `depth` เพิ่ม level ที่เคลียร์ได้ไหม) แล้วผมตั้ง quorum ที่ **2 ใน 3 ถึงจะฆ่า** ซึ่งเป็นกติกาของ refuter แบบ **redundant** (ถามคำถามเดียวกัน N ครั้ง) ไม่ใช่ของ lens ที่ orthogonal — `exists` ไม่มีทางเห็นสิ่งที่ `depth` เห็น

ผลที่วัดได้ตรงตามนั้น: **ไม่มี claim ไหนโดนครบ 3 lens เลย** และมีแค่ 1 ที่โดน 2

```
refute-count distribution: 1 lens = 11 claims · 2 lens = 1 · 3 lens = 0
```
เพราะฉะนั้นตัวเลข `survived 22 / refuted 1` ที่ workflow คืนมา **อ่านไม่ได้** — ต้องอ่านแบบ **OR** (lens ไหนฆ่าก็ตาย) ซึ่งถูกต้องสำหรับ lens ที่ orthogonal

⚠️ CLAUDE.md เขียนคำแนะนำ *perspective-diverse verify* ไว้ แต่ snippet ตัวอย่างข้างบนมันคือ `votes.filter(v => !v.refuted).length >= 2` = quorum แบบ redundant. เอกสารเดียวถือทั้งสองอย่างโดยไม่บอกว่า **เปลี่ยน lens แล้วต้องเปลี่ยน quorum ด้วย** — ผมเดินเข้ากับดักนั้นตรง ๆ

## ผลเมื่ออ่านแบบ OR

**ตาย 12 · รอด 11** (ไม่ใช่ ตาย 1 รอด 22)

| # | claim (ย่อ) | lens ที่ฆ่า | เหตุผล |
|---|---|---|---|
| 1 | Symbolica AI's 'Arcgentica' harness (Agentica SDK, Claude Opus 4.6, 120k context) scores 36.08%… | `exists` | Depends on Claude Opus 4.6, which is not on Kaggle and requires internet at scoring time — both hard constraints violated. The number itself is uncheckable third-party marketing copy from the vendor's… |
| 2 | Symbolica's Arcgentica at 36.08% cost $1,005 vs a plain Claude Opus 4.6 chain-of-thought baseli… | `depth` | Not itself a mechanism — it's a cost/architecture comparison used to argue prioritization, not a build item that clears more levels. It is redundant with claim 1's actual mechanism and doesn't indepen… |
| 3 | Prime Intellect's 'Prime Agent' (RLM = Recursive Language Model architecture) reports clearing … | `exists + depth` | Self-admittedly on a different eval track/metric, not confirmed to be Kaggle hidden set, and the claim text itself flags this. The underlying vendor product is closed/proprietary with no stated Kaggle… |
| 4 | 'Continual Harness' applied to ARC-AGI-3 (foundation model gemini-3.1-pro-preview) scores 20.54… | `exists` | Uses gemini-3.1-pro-preview via API — not a model available on Kaggle, and running it requires internet at scoring time. The number cannot be reproduced under our constraints even though the mechanism… |
| 5 | Continual Harness's own 4-component design (system prompt, memory with confidence-rated facts, … | `depth` | The 62% figure is an execution-cost statistic on ALREADY-SOLVED sub-tasks. Our own diagnosis shows plateaued levels are NOT budget-constrained (comparable action counts to cleared levels), so freeing … |
| 6 | An open-source ARC-AGI-3 harness that requires a graded, falsifiable prediction (e.g. 'cell X,Y… | `exists` | The headline 100.00 RHAE result was produced using Claude Code on Opus 5 — not a model available on Kaggle and requiring internet/API access at scoring time. Although the buildable mechanism (mandator… |
| 7 | An agent that maintains an executable Python world model and simulates a candidate action plan … | `applies` | The paper (arxiv.org/html/2605.05138v2) confirms the three-file executable-world-model architecture and a related failure-mode discussion, but the specific numbers cited do not appear: the paper repor… |
| 8 | The 25 public ARC-AGI-3 games are not a representative depth test: analysis shows 10 of 25 are … | `depth` | A scoping/validity critique of the public eval set, not a mechanism -- it proposes no build item and doesn't itself raise levels cleared; it only tells us which of our own local measurements to trust.… |
| 9 | Forcing a mandatory, falsifiable prediction (which cells/regions change, or noop) before every … | `exists` | This is the same repo/result as an earlier claim, explicitly using Claude Code on Opus 5 — not on Kaggle, requires internet/API access. The RHAE=100.00 result cannot be reproduced under our constraint… |
| 10 | An LLM agent trained to dynamically decide WHEN to spend extra planning compute (vs. act immedi… | `depth` | The claim itself admits its numeric evidence was inaccessible ('numeric deltas not extractable from the abstract alone -- full-text access failed'), leaving no confirmed measurement backing the depth … |
| 11 | Reducing per-instance concurrency to raise per-request token throughput is a measured, real tra… | `depth` | Reallocating GPU capacity to raise per-request tokens/sec is the same throughput lever as our already-closed direction #3 (raising inference throughput via KV-cache fp8), which measured that extra cap… |
| 12 | Speculative decoding in vLLM gives 1.8-2.4x throughput on chat workloads with a well-matched dr… | `depth` | The claim's own 'buildable' field states 'N/A -- documented reason to SKIP'; it is a negative-throughput result offered as a reason NOT to pursue a lever, not a depth mechanism itself.… |

## สิ่งที่ตายคือ *ตัวเลข* ไม่ใช่ *กลไก* — และมันเปลี่ยนอันดับ

candidate อันดับ 1 ของ report (**mandatory prediction gate**) ถูก `exists` ฆ่า ด้วยเหตุผลว่า RHAE=100 ผลิตด้วย Claude Code บน **Opus 5** ซึ่งไม่มีบน Kaggle และต้องใช้ internet — แต่ lens เดียวกันเขียนต่อเองว่า *"Although the buildable mechanism…"*

เพราะฉะนั้นสิ่งที่ถูกหักล้างคือ **หลักฐานว่ามันได้ผล** ไม่ใช่ **ความเป็นไปได้ที่จะสร้าง**. กลไก (บังคับเขียน prediction ก่อนยิง action แล้วให้ harness เกรดด้วย frame diff) ยังสร้างบน Qwen3.8-27B ได้ และไม่ต้องพึ่ง internet เลย

รูปเดียวกันนี้เกิดกับ Symbolica (Opus 4.6), Continual Harness (Gemini 3.1 API), Prime Agent (vendor ปิด) — **ทุกตัวเลขแรง ๆ ในตารางวัดบนโมเดลปิดที่ใหญ่กว่าเรามาก** ซึ่งคือประโยคแรกของ report เองอยู่แล้ว

## ของที่ยังไม่มีใครวัด และเราวัดเองได้ฟรี

report ข้อ 5 ระบุเอง: *"ไม่มี source ไหน (และเราเองก็ยังไม่วัด) แยกว่า plateau มาจาก exploration strategy, perception misread, หรือ genuine reasoning depth"* — นั่นคือการวัดที่ใช้ artifact ที่มีอยู่แล้ว (transcripts + events ของ 25 เกม) ไม่ต้องใช้ GPU slot และไม่ต้องรอ

⚠️ และมีข้อหนึ่งที่กระทบ **v18 ที่กำลังรันอยู่ตอนนี้**: หลักฐานสาย Qwen ที่ report ยกมา (`arxiv.org/html/2604.09687`) อ้างว่า **Qwen3-VL-8B exact-match = 0% ตั้งแต่ grid 4x4** และ text-encoding ชนะ image-encoding 20-55 F1 จุด. ถ้าถ่ายทอดมาถึง 27B ของเรา การขยับ `MULTIMODAL_UPSCALE` 4→8 อาจไม่ขยับอะไรเลย — และการทดสอบที่ถูกกว่าคือถามว่าโมเดล **อ่านภาพออกไหม** ก่อนถามว่าภาพ **ใหญ่พอไหม**. ยังไม่หักล้าง v18 (มันกำลังวัดอยู่) แต่เป็นเหตุผลว่าทำไม perception self-check ควรมาก่อนการจ่าย slot ที่สาม
