# ka59 L2 -- CROSSING TABLE (2026-08-17)

Phase 1 survey: for each (dot, position), a fresh deepcopy from level-2 entry, kicks reproduced via safe_route/safe_kick (harness from ka59_g2_safe_route.py), then click that dot and record the canonical landing + an exhaustive real-BFS census of the piece's post-click reachable component.

| Dot | Setup | Actions | Landing | Phase | Reach(nodes/exh) | ctrl | dot0-appr | dot1-appr | dot2-appr | box0@ph | box1@ph | box3@ph | box2(any) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dot0@entry | entry (no kick) | 1 | (34, 44) | (1, 2) | 23/EXH | True | False | False | -- | False | False | False | False | OK |
| dot0@west | west-kicked (from [(34, 44), (34, 45)]) | 10 | (19, 44) | (1, 2) | 70/EXH | True | False | False | -- | True | False | False | False | OK |
| dot0@chain-north | west+chain-north x0 | 10 | (19, 44) | (1, 2) | 70/EXH | True | False | False | -- | True | False | False | False | OK |
| dot1@entry | entry (no kick) | 1 | (42, 34) | (0, 1) | 76/EXH | True | False | False | -- | False | False | True | False | OK |
| dot1@west | west-kicked (from [(41, 34), (42, 34)]) | 12 | (18, 34) | (0, 1) | 66/EXH | True | False | False | -- | True | False | False | False | OK |
| dot1@chain-north | west+chain-north x0 | 12 | (18, 34) | (0, 1) | 66/EXH | True | False | False | -- | True | False | False | False | OK |
| dot2@entry | entry (no kick) | 1 | (44, 48) | (2, 0) | 60/EXH | True | False | False | -- | False | False | False | False | OK |
| dot2@west | west-kicked (from [(44, 47), (44, 48), (45, 47), (45, 48)]; compound_sweep_of_dot0=True) | 9 | (18, 50) | (0, 2) | 44/EXH | True | False | False | -- | True | False | False | False | OK |
| dot2@chain-north | west+chain-north x0 (compound_sweep_of_dot0=True) | 9 | (18, 50) | (0, 2) | 44/EXH | True | False | False | -- | True | False | False | False | OK |

Total rows attempted: 9 / 9
