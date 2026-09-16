<!-- deep-research wf_8ca69238-c63, 2026-09-10; 26 agents (sonnet search/fetch/verify, opus synth), 4443413 subagent tokens, 597 s; stats {"sources": 54, "fetched": 18, "claims": 51, "survivors": 45, "unverified": 0}; logs ['5 search angles in parallel (sonnet, WebSearch only)', '54 unique sources after dedup', 'dropped 36 lower-ranked sources (cap 18)', '51 claims extracted', 'claims 51: survived 45, refuted 6, unverified 0'] -->

# AGI-style agent for ARC-AGI-3 — what the strong entries do, and what transfers to our base

> ทุกตัวเลขในรายงานนี้มาจาก claim ที่ verify แล้ว หรือจากเลขที่เราวัดเอง (ระบุไว้ว่า "our base") — ค่าประมาณต้นทุนที่ยังไม่ได้วัดจะติดป้าย **ประมาณการ** ไว้ทุกจุด

---

## 1. What the top entries actually do

### Tufa Labs "The Duck" — อันดับ 1 Milestone Prize #1 (public 11.04 บน leaderboard เรา)

- ชนะ Milestone #1 ($37.5K, รอบถึง 30 มิ.ย.) เหนือ Reki และ Md Boktiar Mahbub Murad [g1-1, g1-2 — arcprize.org/blog/arc-prize-2026-milestone-1]
- เป็นรายเดียวในกลุ่มผู้ชนะที่ใช้ **agent-writes-code** [g1-3 — เดียวกัน] — ซึ่งคือ chassis ที่เรารันอยู่แล้ว
- สถาปัตยกรรม: LLM ทำงานใน Python REPL, observation ทุกอย่างเป็น Python variable, action ยิงเข้า env แล้ว env อัปเดต sandbox กลับ [g0-1 — tufalabs.ai/research/duck-harness/] — ตรงกับ bundle aa69123 ของเราแบบตรงตัว
- Perception ใช้ทั้ง image และ text (ascii) ของ grid [g0-2 — เดียวกัน] = `current_frame.segmentation/ascii` ของเรา
- Context สั้นด้วยการ **evict ข้อความเก่าสุดอัตโนมัติ** ไม่มี external memory [g0-4 — เดียวกัน]
- โมเดลเดิมคือ **Qwen 3.6 27B FP8 รันเครื่องตัวเอง** (เคยลอง GPT 5.4 ด้วย) [g0-3, g1-4] — เล็กกว่า stack ~180B MoE ของเราหลายเท่า
- เป้าหมายออกแบบคือ minimal harness ที่ "ถูกกว่าคู่แข่งหนึ่ง order of magnitude ต่อเกม" แลกกับผลไม่สม่ำเสมอ บางเกม "ไม่ผ่านแม้ level แรก" [g0-10 — opinion]

### sonpham-org/arc-3 — fork ที่ instrument ตัว Tufa stack

- reproduce stack Tufa เป๊ะที่ commit `a2dddac`, baseline `tufa-exact-rung0` = **0.679** ทุก knob diff กับตัวนี้ [g0-6 — github.com/sonpham-org/arc-3] (คนละ scale กับ RHAE ของเรา ห้ามเทียบตรง)
- **No-impact detection คือชัยชนะเดียวที่ชัด: +55% (21 vs 15 levels) ที่ action budget เท่ากัน** — ตัด explore action ที่บอร์ดเปลี่ยนเฉพาะแถบ HUD/moves-counter ที่ deterministic [g0-9]
- quant `vrfai compressed-tensors` ชน kernel path พยาธิสภาพบน vLLM 0.25 (ช้ากว่า 0.19 **3.4×**, ngram spec decode ขยายจนใช้ไม่ได้) ขณะที่ spec decode บน official weights เสมอกันเชิงสถิติ [g0-7]
- การแก้ฝั่ง agent ของเขาเอง (required ledger, outline renders, 900s yield) แพงขึ้น **~2.2×** ที่ serving เดิม และสรุปว่า tempo regime ครอบงำทุกอย่าง "ที่ model scale นี้" (27B) [g0-8] — ขัดกับผลวัดของเรา และ scoped ไว้ที่ 27B

### NVIDIA AVO

- **100.00 RHAE บน public set ครบ 183 levels** ด้วย 6,624 environment actions (~265/เกม) [g3-3, g3-4 — developer.nvidia.com] — เป็น public set ล้วน ไม่ใช่ hidden rerun ที่เราถูกตัดสิน จึงเทียบกับ hidden 3.21/3.32/2.68 ของเราไม่ได้
- อ้างว่า architecture ยก model เดิมจาก baseline 30% → 100% [g3-5 — reported]
- มี **supervisor process** เฝ้า trajectory หา stagnation / วนซ้ำไม่ได้ผล แล้ว redirect main agent [g3-6]
- มี **persistent cross-run memory** พก implementation เดิม, eval result, compiler/profiler output, reasoning สะสม [g3-7]

### arXiv 2512.24156 — graph exploration แบบ training-free

- สร้าง directed graph ของ state/transition ที่สำรวจแล้วจาก frame ที่ segment ด้วย vision, จัดลำดับ action ตาม salience [g3-8]
- เลือก action ที่ให้ **shortest path ไปยัง state-action pair ที่ยังไม่เคยลอง** แทนดุลยพินิจของ LLM [g3-9]
- **median 30/52 levels ข้าม 6 เกม, อันดับ 3 private leaderboard ของ Preview Challenge** เหนือ frontier LLM agents [g3-10]
- ผู้เขียนสรุปว่า systematic state tracking + action prioritization สำคัญกว่า learning ใน sparse-feedback env [g3-11 — opinion]
- **code open source** [g3-12]

### NVARC (ARC-AGI-**2**, คนละสนาม)

- 27.64% บน ARC-AGI-2, ที่ 1 Kaggle ARC Prize 2025 public LB, ~20 cent/task [g4-2]; ปฏิเสธโมเดลยักษ์/brute force หันไป synthetic data + test-time training [g4-3]; LoRA + Flash Attention batch 4 บน 103k synthetic puzzles (+ 3.2M augmented) [g4-4]; ไม่เปิดเผย serving/inference อะไรเลย และไม่มีการอ้าง ARC-AGI-3 [g4-5]

---

## 2. เกมทดสอบอะไร และ map กับ loss ที่เราวัดได้

องค์กรผู้จัด: agent ต้อง **explore, infer goals, สร้าง internal model ของ dynamics, และวางแผนลำดับ action เอง** โดยไม่มีคำสั่ง [g3-2]; env เลี่ยงภาษาและ external knowledge ใช้แค่ Core Knowledge priors, calibrate ความยากด้วย human tester [g4-7]; มนุษย์ทำได้ 100% ส่วน frontier AI ต่ำกว่า 1% ณ มี.ค. 2026 [g3-1, g4-6]; 100% แปลว่า "ชนะทุกเกมได้มีประสิทธิภาพเท่ามนุษย์" ไม่ใช่แค่ผ่านครบ [g5-2]; นิยาม AGI ผูกกับช่องว่าง learning efficiency ไม่ใช่คะแนนดิบ [g5-1 — opinion]

กติกาให้คะแนนที่ยืนยันแล้ว ตรงกับสูตรที่เราใช้:
- per level = `(human_baseline_actions / ai_actions)^2` cap ที่ 1.15× baseline [g5-5 — docs.arcprize.org/methodology]
- per game = weighted average ถ่วงด้วยเลข level แบบ 1-indexed → level ลึกมีน้ำหนักมากกว่า [g5-6]
- **level ที่ไม่ผ่าน = 0 และ cap คะแนนทั้งเกม**: ผ่าน 4 จาก 5 → เกมนั้นเกิน 66.7% ไม่ได้ ต่อให้เล่นมีประสิทธิภาพแค่ไหน [g5-7]
- baseline คือ upper-median human (นับ action น้อยสุด) ไม่ใช่ mean [g5-8]

**Map ตรง ๆ**: g5-7 คือคำอธิบายทางกติกาของสิ่งที่เราวัดได้เอง — **90.2 pts/game หายจาก level ที่ไปไม่ถึง เทียบกับ 1.1 จาก action inefficiency**. ทุกแต้มคือ level ไม่ใช่ action ⇒ lever ที่ควรจัดอันดับสูงคือตัวที่ปลดล็อก level ใหม่ ไม่ใช่ตัวที่ลดจำนวน action. ส่วนสองคอขวดที่เราวัดไว้ — click-only stall (hypothesis ผิด/ไม่จบ กิน 30-50 turn/level, perception ตาบอดแค่ 1 ใน 7) และ deep-tail 3 ใน 5 ที่เป็น time-bound (เหลือ <2,000 s ทั้งที่ plan ยัง active) — คือสิ่งที่ g3-6, g0-9, g3-9 ยิงตรงจุดพอดี

---

## 3. LEVERS ranked สำหรับ base ของเรา

หน่วยต้นทุน: 1 public sweep = 25 เกมพร้อมกัน × 7,920 s = **2.2 h wall บน 1 GPU** (คำนวณจากตัวเลข base ของเรา); A/B หนึ่งคู่ ≈ 4.4 GPU-h เทียบ budget 30 GPU-h/สัปดาห์ **build days ทั้งหมดเป็นประมาณการ ยังไม่ได้วัด**

**L1 — No-impact detection (HUD/moves-band mask)** — โจมตี stall loop โดยตรง
- กลไก: ตรวจว่า action ที่ยิงไปเปลี่ยนบอร์ดเฉพาะแถบ HUD/moves-counter ที่ deterministic แล้วไม่นับเป็นความคืบหน้า ตัด wall-press ที่เสียเปล่า [g0-9]
- หลักฐาน: +55% levels (21 vs 15) ที่ action budget เท่ากัน บน harness 27B ของเขา [g0-9]
- ผลที่คาดกับ **levels**: สูงสุดในลิสต์ เพราะกินตรงหมวด loss ที่เราวัด (hypothesis ผิด 30-50 turn/level) และวัดผลเป็น level มาแล้ว — แต่ยังไม่เคยทดสอบบน base เรา และ **ไม่อยู่ใน NULL list (B64-B78)**
- ต้นทุน: build ~1 วัน (ประมาณการ), 4.4 GPU-h สำหรับ A/B หนึ่งคู่
- fits offline rerun: **yes** — โค้ด chassis ล้วน ไม่ต้องมี internet/training data/VRAM เพิ่ม
- smoke ที่ถูกที่สุดที่จะหักล้างได้: รัน 1 เกมที่เรารู้ว่า stall แล้ว log จำนวน action ที่บอร์ดเปลี่ยนแค่แถบ HUD — **ถ้านับได้ ≈0 ครั้ง lever นี้ตายทันทีโดยไม่ต้องยิง sweep** (ต้องมี positive control: เกมที่รู้ว่ามี HUD band)

**L2 — Stall-detector + redirect (supervisor wrapper)** — โจมตี stall loop, กินเวลา tail ด้วย
- กลไก: process แยกเฝ้า trajectory หา stagnation/วนซ้ำ แล้วสั่ง main agent เปลี่ยนสมมติฐาน [g3-6]
- หลักฐาน: เป็นส่วนหนึ่งของระบบที่ทำ 100.00 RHAE / 183 levels บน **public** set [g3-3] — ไม่มีตัวเลข ablation ของ supervisor เดี่ยว ๆ จึงเป็นหลักฐานเชิงโครงสร้าง ไม่ใช่ effect size
- ผลกับ levels: กิน 30-50 turn/level ที่เราวัด และช่วยคืนเวลาให้ deep tail ทางอ้อม
- ต้นทุน: build ~2-3 วัน (ประมาณการ), 4.4 GPU-h/คู่
- fits offline: **yes** — wrapper รอบ loop เดิม ไม่มี training data, อยู่ในงบ action/time เดิม
- smoke ที่ถูกที่สุด: offline replay บน trajectory ที่บันทึกไว้แล้ว — ถ้า detector ไม่ยิงในช่วง 30-50 turn ของ stall ที่เรารู้จัก (และไม่ยิง false บน level ที่ผ่านลื่น ๆ) ก็จบ ไม่ต้องใช้ GPU เลย

**L3 — Graph state-tracking + shortest-path-to-untested (open source)**
- กลไก: directed graph ของ state/transition จาก frame ที่ segment แล้ว + เลือก action ที่ path สั้นสุดไป state-action ที่ยังไม่เคยลอง แทนดุลยพินิจ LLM [g3-8, g3-9]
- หลักฐาน: median 30/52 levels, อันดับ 3 private LB ของ **Preview Challenge** [g3-10]; ผู้เขียนชี้ว่า state tracking สำคัญกว่า learning [g3-11]; **code เปิด** [g3-12]
- ผลกับ levels: ตรงกับผลวัดของเราว่า turn ไม่ได้ถูกจำกัดด้วย generation (8 s/turn ที่ 3-way) — คอขวดคือ hypothesis ไม่ใช่ token
- ต้นทุน: build ~2-4 วัน integration เข้า python tool (ประมาณการ), 4.4 GPU-h/คู่ + ต้อง vendor โค้ดลง bundle ก่อน rerun
- fits offline: **yes** (training-free, deterministic, ไม่ต้องต่อเน็ตตอน inference)
- smoke: รัน graph explorer เดี่ยว ๆ แบบไม่มี LLM บน 1 เกมสาธารณะที่เรา stall — ถ้าจำนวน state ที่ visit ไม่โตหรือมันวนซ้ำ state เดิม แปลว่า segmentation ของเรา feed graph ไม่ได้ → หักล้างก่อนจ่าย GPU

**L4 — Kernel-path sanity check ของ quant × vLLM dev build × MTP-3** — โจมตี time-bound tail
- กลไก: ยืนยันว่า NVFP4 + vLLM dev + MTP-3 ไม่ได้ตกลง kernel path พยาธิสภาพ เพราะเคสที่บันทึกไว้ให้ **3.4× ช้ากว่า** และ spec decode ขยายจนใช้ไม่ได้ [g0-7]
- ผลกับ levels: ทางอ้อมแต่แรง — deep-tail 3 ใน 5 ที่เราเสียเป็น time-bound; ตอนนี้เราโยนความช้า 300 s/action ที่ 25-way ให้ "server queueing + unbounded python tool loop" ซึ่ง kernel regression ปลอมตัวเป็นอาการเดียวกันได้
- ต้นทุน: build ~0.5 วัน (ประมาณการ), micro-benchmark ไม่ถึง 1 GPU-h
- fits offline: **yes** (เป็นการวัด ไม่ใช่ feature)
- smoke: จับเวลา token/s ของ request เดี่ยว MTP-3 on vs off ที่ concurrency 1 — ถ้าเท่ากันหรือ MTP ชนะ ก็ไม่มี kernel pathology ให้ตาม (B78 เคยวัด MTP off เป็น NULL ที่ระดับ **คะแนน** ไม่ใช่ระดับ throughput เดี่ยว จึงยังไม่ซ้ำ)

**L5 — สลับ serving ลงมาที่ ~27B FP8** — จัดอันดับต่ำ
- กลไก: โมเดลเบากว่ามาก ใส่ 96 GB สบาย ไม่ต้อง training data [g1-4, g0-3]
- แต่: B69 (serving swap) คือ lever เดียวที่เคยผ่าน p<0.05 บน base เรา และมันชนะ *ขึ้น* ไม่ใช่ลง; ไม่มีตัวเลข quality ของ 27B บนสนามเราเลย
- ทำก็ต่อเมื่อ L4 พบว่าคอขวดคือ wall-clock จริง ๆ และต้องแลกคุณภาพเอาเวลา

**Priced NULL บน base เราแล้ว — อย่าเปิดใหม่**: anim chassis (B71), ACTION7/undo mapping (B76), completion cap (B75), MTP off (B78), Gemma-31B swap (B64), prompt-side breakers (B70 + 11 ตัวก่อนหน้า). โดยเฉพาะข้อสรุปเรื่อง **tempo regime / yield** ของ sonpham [g0-8] อย่าเอามาเป็นเหตุผลรื้อ knob เหล่านี้ — เขา scope ไว้ที่ 27B dense ชัดเจน และผลวัดของเราขัดกันตรง ๆ

**บล็อกด้วยข้อจำกัด (ไม่ต้องพิจารณา)**: persistent cross-run memory + compiler/profiler loop ของ AVO [g3-7] = รื้อ harness ไม่ใช่ drop-in; synthetic data + LoRA fine-tune แบบ NVARC [g4-3, g4-4] = เราไม่มี training data นอกจาก 25 เกมสาธารณะ

---

## 4. What is NOT known

- **ไม่มี hidden-set number ของใครเลย** นอกจากของเราเอง — AVO 100.00 เป็น public set ล้วน [g3-3] และ BenchLM เป็นคนละบริบทการให้คะแนน (aggregate ของ frontier chat model, ไม่มี Kaggle team/serving stack เลย) [g2-5]
- **ไม่รู้ว่า 6,624 actions ของ AVO ใช้เวลาเท่าไหร่** — ไม่มีตัวเลข wall-clock ต่อ action จึงบอกไม่ได้ว่าลงกรอบ 7,920 s / 25-concurrent ของเราไหม [g3-4]
- **ไม่มี ablation ของ supervisor เดี่ยว ๆ** — 30% → 100% ถูกอ้างเป็นผลของ "ทั้งระบบ" [g3-5]
- **NVARC ไม่เปิดเผย serving/inference/GPU/quant ใด ๆ** และไม่แตะ ARC-AGI-3 → เทียบกับ B69 ไม่ได้ทั้งยืนยันและหักล้าง [g4-5]
- **No-impact detection และ graph method วัดบนคนละ harness/คนละชุดเกม** (27B ของเขา / Preview Challenge) → effect size ไม่ถ่ายโอน ต้อง A/B บน base เราเอง [g0-9, g3-10]
- **หน้า methodology ที่ดึงมาไม่มี 2026 revision ของ RHAE สำหรับ imperfect-information path** — ยืนยันหรือปฏิเสธไม่ได้ อาจอยู่ที่อื่นหรือยังไม่เผยแพร่ [g5-9]; หน้า landing ของ ARC-AGI-3 ไม่มีตัวเลขเชิงปริมาณเลย [g5-10]
- **สองแหล่งดึงไม่ขึ้น**: x.com/tufalabs (HTTP 402) [g1-5] และ Kaggle discussion 717133 (SPA ไม่มี body) [g1-6] — เนื้อหาในนั้นยังไม่ถูกประเมิน
- **ยังไม่รู้ว่า throughput 300 s/action ของเราเป็น queueing, python tool loop หรือ kernel path** — L4 คือสิ่งที่แยกสามอย่างนี้ และยังไม่มีใครทำ
