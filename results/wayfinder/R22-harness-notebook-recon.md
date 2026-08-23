# รายงานผลการค้นคว้า: ใครวิ่ง notebook ไหนเหนือเราบน leaderboard ARC-AGI-3

## หมายเหตุวิธีวัด (สำคัญ อ่านก่อน)

รอบนี้ verifier ทั้ง 3 ตัวถามคนละคำถาม (exists / attribution / usable) — claim ใดถูก **ตัวใดตัวหนึ่ง**หักล้างก็ตายทันที (OR logic) ไม่ใช่ต้อง 2-ใน-3 เห็นตรงกัน (quorum แบบเดิมที่เจอปัญหาในรอบก่อนคือฆ่าอะไรแทบไม่ได้เลย — โครงสร้างผิด ไม่ใช่ผลลัพธ์ที่ผิด). ผลคือ 15 claims รอด / 6 claims ตาย — 2 ใน 6 ที่ตายเป็น **attribution failure ล้วนๆ**: มีแหล่งจริง แต่แหล่งนั้นไม่ได้พิสูจน์สิ่งที่ claim อ้าง

---

## (1) คำตอบบรรทัดเดียว: ทีมที่ได้ 2.4-3.6 รัน notebook/fork ไหน?

**หาไม่เจอ — การค้นหาวันนี้ไม่สามารถผูกชื่อทีมใดใน cluster 2.4-3.6 (cstl, Tufa Labs, wking edewd, rellik13, ฯลฯ) เข้ากับ notebook, fork หรือ repo ที่เจาะจงได้เลยแม้แต่ทีมเดียว.** สิ่งที่ค้นเจอคือ**พื้นที่ทางเลือกของสถาปัตยกรรม** (Duck-family 3 fork + VLM-family 2 notebook, ดูตารางข้อ 2) ไม่ใช่หลักฐานว่าใครวิ่งอะไร — claim ที่พยายามผูก "cstl"/"Daniel Franzen" เข้ากับ source ใดๆ ถูกฆ่าเพราะหา attribution ไม่ได้จริง (ดูข้อ 4)

---

## (2) Claims ที่รอด แยกตามคำถาม A-E

### A — Notebook/fork ที่มีการ publish จริง (สถาปัตยกรรมทางเลือก ไม่ใช่หลักฐานว่าทีมไหนใช้)

| Claim | แหล่ง |
|---|---|
| "The Duck" (Tufa Labs, Milestone-1 winner, Qwen บน Python-REPL loop) — notebook publish โดย jeroencottaar บน Kaggle | https://arcprize.org/blog/arc-prize-2026-milestone-1 |
| "Reki" (Milestone-1 อันดับ 2) — VLM (Gemma-4-31B local) มองภาพ board แล้วคืน JSON action เดียวต่อ turn, มี reflection memory + legal-action guard — คนละสถาปัตยกรรมกับ Duck โดยสิ้นเชิง (ไม่ใช่ Python-REPL) | https://www.kaggle.com/code/ruichardliu/milestone1-2nd-solution |
| "forge" (Md Boktiar Mahbub Murad, Milestone-1 อันดับ 3) — VLM framework + reflection memory เช่นกัน (สาย Reki) | https://www.kaggle.com/code/mbmmurad/arc-agi-3-lb-0-86-3rd-place-candidate-milestone |

### B — Fork อื่นของ TAAF/Duck ที่เรายังไม่เคยเห็น

| Claim | แหล่ง |
|---|---|
| sonpham-org/arc-3 — fork อิสระที่ 2 (แยกจาก thtennant ที่รู้จักแล้ว), track จาก upstream commit `a2dddac`, ทุก diff เป็น reviewed commit แยก | https://github.com/sonpham-org/arc-3 |
| sonpham-org มี extension folder ของตัวเอง `vendor-taaf-grafts/taaf_grafts/` — 11 module, ซ้อนทับบางส่วนกับ thtennant's 18-module/6,524-line taaf-grafts (ชื่อร่วม: banking_solver, recovery, retry_guard, shortcircuit_solver, transfer_solver+family_store, agent_ext — แต่ **ไม่มี** goalkeep/clickmap/searchmap/schema_void/hudmask) | https://github.com/sonpham-org/arc-3 |
| sonpham-org รายงาน local benchmark: config `ffa7gn` = 1.62 (ex-ft09) เทียบ baseline-v12 = 1.21 — lever ใหญ่สุดคือ **"no-impact action detection"** (ข้าม explore action ที่แตะเฉพาะ HUD element ที่ deterministic) claim +55% | https://github.com/sonpham-org/arc-3 |
| Tufalabs/duck-harness — **repo ทางการ** ของทีม Tufa Labs เอง (ไม่ใช่ fork ต่อ) มี Kaggle notebook ที่ root ที่ reproduce การรันจริงบน 25 official games | https://github.com/Tufalabs/duck-harness |
| StochasticGoose (Dries Smit, Tufa Labs) — CNN action-prediction + RL แยกจาก Duck ทั้งหมด, ชนะ preview competition (12.58%) แต่คะแนนร่วงเหลือ 0.25% พอ ARC-AGI-3 เต็มรูปเปิดตัว | https://medium.com/@dries.epos/1st-place-in-the-arc-agi-3-agent-preview-competition-49263f6287db |

### C — มีใครพูดถึงปัญหา level-transition wipe / state-carry-over บ้างไหม

| Claim | แหล่ง |
|---|---|
| **Continual Harness (Princeton, Seth Karten et al.)** — harness ที่ตั้งใจไม่ล้าง state ตอน level-up/game-over/stagnation: "Refiner" อ่าน trajectory ดิบซ้ำแล้ว consolidate เป็น memory/skill/subagent แทนการทิ้ง — ได้ 20.54% public ที่ต้นทุน $774 (เทียบ baseline OpenClaw/Opus 4.7 5.2%, A-Evolve MAS 12.30%) | https://sethkarten.substack.com/p/continual-harness-an-efficient-self |
| **OpenAI ยืนยันเอง** — official harness ทิ้ง private reasoning ทุก action และลบ history เก่าทิ้งจริงเมื่อเกิน 175,000 chars; ปิดการทิ้งนี้ (retained reasoning + compaction) ทำให้ GPT-5.6 Sol คะแนน public 3x (13.3%→38.3%) พร้อม output token ลด 6x | https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/ |
| BentoLabs (YC) — ปัญหาคนละ granularity (cross-**run** ไม่ใช่ cross-**level**): agent เริ่มจากศูนย์ทุกรอบ, retrieval+"nudge" layer เตือนสิ่งที่เคยเจอ ยก RHAE 1.27%→3.32%, levels 16→22 | https://bentolabs.ai/blog/self-learning-ai-agents-arc-agi |

### D — 110 hidden runs คือ clone ของ 25 public games วนไหม

| Claim | แหล่ง |
|---|---|
| **ไม่ใช่** — arXiv technical report (Table 1): Public Demo 25 / Semi-Private 55 / Fully Private 55 = 135 รวม, **ไม่ overlap กัน**, และ private sets ถูกออกแบบให้เป็น out-of-distribution เจตนา ("limited overlap with the mechanics found in the public environments") | https://arxiv.org/html/2603.24621v1 |
| DataCamp คอนเฟิร์มโครงสร้างเดียวกันอิสระ: 135 total, 25 public, ที่เหลือคือ semi-private+fully-private (ไม่ใช่ clone) | https://www.datacamp.com/blog/arc-agi-3 |

### E — Tufa Labs พูดอะไรเกี่ยวกับ 3.04 บ้าง

| Claim | แหล่ง |
|---|---|
| Duck harness ทางสถาปัตยกรรม: ไม่มี fixed reset point เลย — ใช้ "infinite play via eviction" (ลบ message เก่าสุดออกเรื่อยๆ เพื่อคุม context window แทนการรีเซ็ต) | https://tufalabs.ai/research/duck-harness/ |
| **ไม่มีแหล่งไหนอธิบายว่า Tufa Labs ไปจาก Milestone-1 (~1.6) ถึง 3.04 บน live leaderboard ตอนนี้ได้อย่างไร** — blog เดียวที่มีหยุดที่ผลลัพธ์ Milestone-1 เท่านั้น, ARC Prize เองก็ระบุชัดว่า "No Claims About...post-milestone improvements" | https://tufalabs.ai/research/duck-harness/ |

---

## (3) สิ่งที่ควรเปลี่ยนแผนสร้าง

**สรุปสั้น: bug ที่เราเจอเอง (tool_agent.py:1347-1356 ล้าง world_model/goal_model ทุก level_transition) คือ class เดียวกับสิ่งที่ทั้ง Princeton และ OpenAI วัดผลกระทบไว้แล้วจริง — และตัวเลขที่ OpenAI วัดคือ 3 เท่า**

1. **Priority สูงสุด — แก้ level-transition wipe.** OpenAI วัดว่าการทิ้ง state (คนละ mechanism แต่ class เดียวกัน: ทิ้ง reasoning ทุก action + ลบ history เก่าดิบๆ) กดคะแนนจาก 38.3%→13.3% (เกือบ 3x). Princeton แก้ปัญหาเดียวกันตรงจุด (level-up/game-over/stagnation) ด้วย Refiner ที่ consolidate แทนทิ้ง แล้วได้ 20.54% เทียบ baseline 5.2-12.3%. **แพทเทิร์นที่ port ได้จริงแม้ไม่มี internet ตอน scoring**: แทนที่จะ set world_model/goal_model/... = "" ตรงๆ ที่บรรทัด 1347-1356 ให้ distill สรุปสั้นจาก state เดิมก่อนล้าง (retain-then-summarize แทน discard) — implement ได้ offline ล้วนๆ ไม่ต้องพึ่ง API พิเศษของใคร

2. **หยุดคิดว่า local 25-game score เป็นตัวแทนของ hidden scoring pool** — arXiv ยืนยันคู่แหล่งว่า 55+55 fully/semi-private เป็นคนละ environment กับ 25 public, ออกแบบให้ out-of-distribution เจตนา. อะไรก็ตามที่ tune จนเก่งขึ้นเฉพาะบน 25 public games (เช่น recovery/goalkeep/banking-solver ที่ tune ไปกับ quirk การ์ดใดการ์ดหนึ่ง) มีความเสี่ยงไม่ transfer ไปยัง hidden pool เลย — ให้ priority กับ fix ที่ mechanic-agnostic (เช่น state-preservation ข้างบน) เหนือ heuristic เฉพาะการ์ด

3. **lever ทดลองต้นทุนต่ำที่ยังไม่เคยลอง: "no-impact action detection"** จาก sonpham-org (ข้ามการยิง explore action ที่แตะแค่ HUD/deterministic element) — claim +55% ex-ft09 ในเบนช์ท้องถิ่นของเขาเอง (294-game custom catalog, **ไม่ใช่** official 25-game commit-run เดียวกับที่เราใช้ ดังนั้นตัวเลขไม่เทียบตรงกับ 1.70 ของเรา) แต่เป็นแนวคิดที่คนละทางจาก lever ที่เราปิดไปแล้วทั้งหมด (output cap, brevity, KV fp8, per-turn diff push) — คุ้มลอง A/B แบบควบคุมก่อนเชื่อตัวเลข +55%

4. **Reki/forge (VLM + JSON action ต่อ turn, ไม่มี live REPL loop) เป็นทางเลือกสถาปัตยกรรมสำรอง** ถ้า Duck-family efficiency lever ยังชนเพดาน 5.80 public ตามที่ปิดไปแล้ว — ยังไม่ต้องทำตอนนี้ แต่บันทึกไว้เป็นทางถัดไป

---

## (4) แต่ละ lens ฆ่าอะไร และทำไม

| Claim ที่ตาย | Lens ที่ฆ่า | เหตุผล |
|---|---|---|
| Long-tail notebooks (nihilisticneuralnet, quantumized, gourabr0y555 ฯลฯ) เป็นหลักฐานว่า leaderboard tail รันสาย non-LLM | **exists** + **attribution** | gourabr0y555 notebook **ไม่มีชื่อ**อย่างที่ claim อ้าง (fetch ตรงยืนยันว่า fabricated title) — และต่อให้ notebook มีอยู่จริงทั้งหมด การที่มันโผล่ใน code search **ไม่ใช่**หลักฐานว่ามี team ไหนบน leaderboard ใช้มันจริง (popularity/discoverability ≠ attribution) |
| ทีม 1.70 มี "7 ทีมอื่น" ที่ผูกไม่ได้กับ source ใดๆ | **attribution** | ตัวเลขขัดกับ context ที่ตั้งไว้แล้วว่ามี **6** ทีม ไม่ใช่ 7 — internal error ในตัว claim เอง |
| thtennant fork ก็ point กลับไปยัง dataset `taaf-kaggle-source-share` ของ jeroencottaar เหมือนกับ sonpham-org | **attribution** | มีแต่ sonpham-org ที่ evidence ยืนยันตรงๆ ว่า cite dataset นี้เป็น upstream — ของ thtennant เป็นแค่การเดาจากชื่อ dataset คล้ายกัน ไม่มีแหล่งยืนยันจริง |
| "official Kaggle-facing leaderboard ใช้ semi-private set" | **attribution** + **usable** | arXiv พูดแค่ "the official leaderboard" เฉยๆ ไม่ได้ระบุว่าเป็น Kaggle competition scoring หรือ arcprize.org public leaderboard — ตาม taxonomy ในรายงานเดียวกัน scoring บน Kaggle จริงๆ ควรมาจาก fully-private (กัน leak) ไม่ใช่ semi-private ที่ claim อ้าง — claim เองก็ flag ความไม่ชัวร์นี้ไว้ |
| Duck harness บอกว่า hand-crafted tools "ทำให้แย่ลง" | **exists** | fetch ตรง 2 ครั้งจาก source_url ที่อ้าง ไม่พบข้อความนี้เลย — เป็น paraphrase จาก search summary (น่าจะมาจาก X thread อื่น) ไม่ใช่จาก blog ที่ cite |
| Tim Scarfe สัมภาษณ์ Tufa Labs 2 ตอน (technical + broader) | **exists** + **attribution** + **usable** | source_url เป็นหน้า X profile ทั่วไปที่ fetch ไม่ได้ (402) — รายละเอียด "2 ตอน" มาจาก search summary สังเคราะห์เอง ไม่ใช่ quote จากหน้าไหนที่ verify ได้จริง |

**บทเรียนซ้ำที่เห็นชัดในรอบนี้: "มีอยู่จริง" (exists) กับ "เป็นหลักฐานของสิ่งที่อ้าง" (attribution) เป็นคนละคำถาม** — 3 ใน 6 ที่ตายมี source จริงรองรับ แต่ source นั้นพิสูจน์คนละเรื่องกับที่ claim เขียน (1,275 downloads ของ thtennant fork คือ popularity ไม่ใช่หลักฐานว่า scoring team ใดใช้มัน — จุดที่โจทย์เตือนไว้ตรงๆ)

---

## (5) คำถามที่ยังเปิดอยู่

- **ไม่มีทีม 2.4-3.6 ทีมไหนเลยที่ผูก source/notebook ได้** (cstl, Tufa Labs ปัจจุบัน 3.04, wking edewd, rellik13 ฯลฯ) — นี่คือ gap ที่ค้นวันนี้ปิดไม่ได้ ไม่แนะนำเสียเวลาค้นซ้ำทางเดิม
- **Tufa Labs ไปจาก 1.6 (Milestone-1) → 3.04 (live) ได้อย่างไร ยังไม่มีแหล่งสาธารณะอธิบาย** — ทางเดียวที่เหลือคือไล่ดู commit/tag ใน `Tufalabs/duck-harness` repo ว่ามีอะไรใหม่กว่า Milestone-1 release หรือไม่ (ยังไม่ได้ไล่)
- **Kaggle competition scoring ใช้ semi-private หรือ fully-private set กันแน่** — claim นี้ถูกฆ่าเพราะ evidence ไม่ชัด ต้องหา confirmation อีกรอบ (อาจจากหน้า official competition rules บน Kaggle เอง ไม่ใช่ arXiv paper)
- **sonpham-org's +55% no-impact-detection number วัดบน local 294-game catalog ไม่ใช่ official 25-game commit-run** — ยังไม่รู้ว่าจะ transfer มาเป็นตัวเลขเท่าไหร่บน setup ของเรา ต้อง A/B เอง
- **thtennant fork's ต้นทาง upstream ยังไม่ยืนยันแน่ชัด** (แค่คาดจากชื่อ dataset คล้ายกัน) — ถ้าอยากรู้จริง ต้องเปิดอ่าน fork นั้นตรงๆ ว่า cite อะไรไว้