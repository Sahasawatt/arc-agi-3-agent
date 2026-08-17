"""diag: colour-10 components after a few UP presses from L5 entry, to
diagnose why band_row() reads None going UP.  Scratch probe, not a formal
result -- kept as ar25_u4_diag.py per the ar25_u4* naming rule."""
import copy
from collections import deque
import numpy as np
import arc_agi
from arcengine.enums import GameState
import mirror

A = None
def step(env, v, data=None):
    global A
    if A is None:
        A = {a.value: a for a in env.action_space}
    return env.step(A[v], data=data) if data else env.step(A[v])

def grid(o):
    if o is None: return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]

def components(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                cells, q = [], deque([(y, x)])
                seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny, nx = cy+dy, cx+dx
                        if 0<=ny<H and 0<=nx<W and mask[ny,nx] and not seen[ny,nx]:
                            seen[ny,nx]=True
                            q.append((ny,nx))
                ys=[c[0] for c in cells]; xs=[c[1] for c in cells]
                out.append({"n":len(cells),"bbox":(min(ys),max(ys),min(xs),max(xs))})
    out.sort(key=lambda c:-c["n"])
    return out

def get_to_l5():
    env = arc_agi.Arcade().make("ar25")
    obs = env.reset()
    d = mirror.Mirror({a.value for a in env.action_space})
    acts=0
    while obs.levels_completed<4 and acts<400:
        v = d.act(grid(obs), obs.levels_completed)
        if v is None: break
        obs = step(env,int(v)) if not isinstance(v,tuple) else step(env,6,{"x":int(v[1]),"y":int(v[2])})
        acts+=1
        if obs is None: break
        if obs.state==GameState.GAME_OVER: obs=env.reset()
    assert obs.levels_completed==4
    return env,obs

env,obs = get_to_l5()
g = grid(obs)
mask = (g==10).copy(); mask[:,62:]=False; mask[62:,:]=False
print("ENTRY colour10 components:", components(mask))

for i in range(5):
    o = step(env, 1)  # UP
    if o is None:
        print(f"up{i}: obs None"); break
    print(f"up{i}: state={o.state} lvl={o.levels_completed}")
    g = grid(o)
    mask = (g==10).copy(); mask[:,62:]=False; mask[62:,:]=False
    print(f"  colour10 comps: {components(mask)}")

print("\n--- now check DOWN past phase11 (48-50) to see the true down clamp ---")
env2, obs2 = get_to_l5()
for i in range(15):
    o = step(env2, 2)  # DOWN
    if o is None:
        print(f"down{i}: obs None"); break
    g = grid(o)
    mask = (g==10).copy(); mask[:,62:]=False; mask[62:,:]=False
    print(f"down{i}: comps={components(mask)}")

print("\n--- frame byte-equality check across the merged UP steps ---")
env3, obs3 = get_to_l5()
frames=[]
for i in range(4):
    o = step(env3, 1)
    frames.append(grid(o))
for i in range(1,len(frames)):
    print(f"up{i-1} vs up{i}: equal={np.array_equal(frames[i-1],frames[i])}")

print("\n--- frame byte-equality check across the merged DOWN steps (11,12,13) ---")
env4, obs4 = get_to_l5()
dframes=[]
for i in range(15):
    o = step(env4, 2)
    dframes.append(grid(o))
for i in [10,11,12,13]:
    print(f"down{i} vs down{i+1}: equal={np.array_equal(dframes[i],dframes[i+1])}")
