ต่อโปรเจกต์ ARC-AGI-3 ที่ Desktop\projects\arc-agi-3-agent (public MIT-0,
github.com/Sahasawatt/arc-agi-3-agent, master = 2170b73 = origin/master, 202 tests เขียว,
tracked tree สะอาด — jsonl/log ค้าง untracked ลบได้)

อ่านก่อนเริ่ม: CLAUDE.md (กติกา + traps — ส่วนด่าน 7 อยู่ท้าย ๆ ของ traps) แล้ว
README.md ตั้งแต่ "### 844 to 570" ลงไป · results/l7-model.md ทั้งไฟล์ (มี CORRECTION
คั่นกลาง — อย่าอ่านครึ่งบนแล้วหยุด)

สถานะ: ls20 6/7 [23, 45, 99, 178, 292, 209] = 40.503% (baseline 22,123,73,84,96,192)
  ด่าน 6 = 1.09x baseline (cap 115 ที่ 179 — เหลือ 30 actions = +13.4 ถ้าอยากเก็บ)
  cd82 1213 (แพงขึ้น 179 จาก unframed-plate reader — แลกกับด่าน 7 เล่น lock ได้,
  วัดและจดไว้แล้ว ชั่งใหม่ได้) · m0r0 53 · ar25 173 · อีก 13 เกม 0 ด่าน · BUDGET=2000

เป้ารอบนี้: ผ่านด่าน 7 (weight 7/28 — ผ่านได้ = +7 game points ขั้นต่ำ)

โมเดลด่าน 7 (วัดครบแล้ว ห้าม re-diagnose — รายละเอียด+พิกัด results/l7-model.md):
  frame = หน้าต่าง 40x40 รอบ piece บนโลกพิกัดคงที่ · เครื่อง lock เดียวกับด่าน 6
  แต่ชิ้นส่วนห่างกันเกินหนึ่งหน้าต่าง — indicator glyph ไร้กรอบ (อ่านได้แล้ว) ·
  ink changer นิ่งที่ x11-12 y41-43 เดิน alphabet ที่ Gate.legacy รู้แล้ว (กด 3 ครั้ง
  ถึง ink 8 ฟรี) · shape changer = patroller 2 ตัว (ตัวซ้าย x20-22 เดิน ALPHABET,
  ตัวขวา x55-57 quarter turn) · ask = (8, #.#/##./.##) วาดเป็นรูปในหลุม void
  ⚠️ "ประตู" x28-34 y49-55 คือ HOLE ไม่ใช่ lock — อะไรจบด่านจริงยังไม่พิสูจน์
  · ชีวิต 21 actions, 3 ชีวิต (hud สี 8 = ชีวิต×4), ตายที่ 3 = gameover ล้าง movers

โครงสร้างที่ ship แล้ว (อยู่ใน master): fog latch (displacement-based, 2 ก้าวติด) ·
stitch + dirty mask (cell เคยเปลี่ยน = ห้ามวาดจากความจำ) · max_missed 200 ตอน windowed ·
learn-on-mute gated ด้วย gate.windowed (ungated เสียด่าน 5+6 — วัดสองแบบแล้ว ห้ามแกะ) ·
trace filter 3 ชั้นตอน windowed (fog-out / fog-in / occlusion) กัน refills() ถอนสี 11

ตัวเลขล่าสุดด่าน 7 (จากรัน 209): budget เหลือ ~1154 · ตาย ~31 (20 starve+11 gameover) ·
chg ~15 · moving-learn 139 · tank=[11] 196/345 รอบ (57%) · fuels>0 118 รอบ

คำถามรอบนี้ ตามลำดับ:
  1. learn trip weave refill หรือยัง — ARC_ACCT รันเดียว เทียบ deaths/chg กับ 31/15
     ถ้ายังตายถี่: ทำไม route_moving ไม่ weave ทั้งที่ fuels ไม่ว่าง (สงสัย: refill
     อยู่นอกหน้าต่าง — stitch วาดให้แล้ว แต่ `targets()`/`seen` เห็นไหม ยังไม่เคยเช็ค)
  2. tank ว่าง 149 รอบที่เหลือ = ต้นด่าน+หลังตาย — seed จาก pickup แรกให้ถาวรทั้งด่าน?
     (ระวังรั่วไปด่านอื่น)
  3. shape alphabet ของ patroller ตัวซ้ายยังไม่มี edge ใน mover_edges — learn trip
     ต้องพาไปกดซ้ำจน alphabet เดินถึง #.#/##./.##
  4. เครื่องมือ: probe7.py (census / -map stitch / glyph readout) · ARC_RMDBG มี lvl= แล้ว ·
     prefix ถึงด่าน 7 สร้างจาก out-*.jsonl field "v" (1207 actions)

ข้อจำกัด: ห้ามอ่าน environment_files/ (เฉลย) · ห้าม git add -A · ถามก่อน commit ·
rtk ทำ pytest+grep เพี้ยน — redirect ลงไฟล์แล้วอ่านด้วย python · ทุกการแก้: sweep
ls20+cd82+m0r0+ar25 ก่อน/หลัง ห้ามเกมไหนเสียด่าน ทีละการแก้ · เสียด่าน/inert = revert
ทันที ความรู้ลง docs · ตัดสินจาก accounting ห้าม hunch · background bash ต้อง cd เข้า
repo เอง · sweep ~10-15 นาที — รันเป็น background task รอ notification อย่า poll ถี่
