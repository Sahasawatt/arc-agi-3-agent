"""ka59 w5 -- quick check: does a NORTH kick on dot0 from its raw entry
position (before any west kick) stay within piece-reachable territory,
so west+north could both be done pre-crossing?
    ./.venv/Scripts/python.exe ka59_w5.py > results/ka59-w5.txt
"""
import copy, sys
from collections import deque
import numpy as np
import arc_agi
from arcengine.enums import GameState
import ferry

def grid(o):
    if o is None: return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]
def piece_xy(g): return ferry.find_cell(g, 0) if g is not None else None
def dot_cells(g):
    ys, xs = np.nonzero(g[:63] == 5)
    return sorted(zip(xs.tolist(), ys.tolist()))
def phase(p): return None if p is None else (p[0]%3, p[1]%3)
def region(x0,x1,y0,y1): return lambda p: x0<=p[0]<=x1 and y0<=p[1]<=y1
def bfs_route(env,obs,is_target,avoid=(),action_values=(1,2,3,4),max_nodes=1500):
    avoid=set(avoid); p0=piece_xy(grid(obs))
    if p0 is None: return None,None,None
    if is_target(p0): return [],env,obs
    seen={p0}; q=deque([(p0,env,obs,[])]); nodes=0
    while q and nodes<max_nodes:
        pos,e,o,path=q.popleft(); nodes+=1
        for v in action_values:
            e2=copy.deepcopy(e); o2=e2.step(A[int(v)])
            if o2 is None or o2.state==GameState.GAME_OVER: continue
            p2=piece_xy(grid(o2))
            if p2 is None or p2 in seen or p2 in avoid: continue
            seen.add(p2); newpath=path+[v]
            if is_target(p2): return newpath,e2,o2
            q.append((p2,e2,o2,newpath))
    return None,None,None
def exhaustive(env,obs,max_nodes=15000):
    p0=piece_xy(grid(obs)); seen={p0}; q=deque([(p0,env,obs)]); nodes=0
    while q and nodes<max_nodes:
        pos,e,o=q.popleft(); nodes+=1
        for v in (1,2,3,4):
            e2=copy.deepcopy(e); o2=e2.step(A[int(v)])
            if o2 is None or o2.state==GameState.GAME_OVER: continue
            p2=piece_xy(grid(o2))
            if p2 is None or p2 in seen: continue
            seen.add(p2); q.append((p2,e2,o2))
    return seen,nodes
def reach_l2():
    env=arc_agi.Arcade().make("ka59")
    global A
    A={a.value:a for a in env.action_space}
    obs=env.reset(); drv=ferry.Ferry(None); n=0
    while obs.levels_completed<1 and n<200:
        v=drv.act(grid(obs),obs.levels_completed)
        obs=(env.step(A[6],data={"x":int(v[1]),"y":int(v[2])}) if isinstance(v,tuple) else env.step(A[int(v)]))
        n+=1
    assert obs.levels_completed==1
    return copy.deepcopy(env),obs

ENV0,OBS0=reach_l2()
cur_e,cur_o=copy.deepcopy(ENV0),OBS0
dots0=dot_cells(grid(cur_o))
D0=[c for c in dots0 if 33<=c[0]<=35]
D1=[c for c in dots0 if 40<=c[0]<=43]
D2=[c for c in dots0 if c[0]>=44]
print(f"entry dot0={D0}")

# approach from south of dot0, press north
x0=min(c[0] for c in D0); x1=max(c[0] for c in D0)
y0=min(c[1] for c in D0); y1=max(c[1] for c in D0)
p,_,_=bfs_route(copy.deepcopy(cur_e),cur_o,region(x0-1,x1+1,y1+2,y1+7),avoid=D1+D2)
if p is None:
    print("no south approach to dot0"); sys.exit(0)
for v in p: cur_o=cur_e.step(A[v])
print(f"approached from south, piece={piece_xy(grid(cur_o))}")
before=set(dot_cells(grid(cur_o)))
cur_o=cur_e.step(A[1])
d0_now=[c for c in dot_cells(grid(cur_o)) if c not in D1 and c not in D2]
print(f"after north-kick: piece={piece_xy(grid(cur_o))} dot0={d0_now} (entry was {D0})")

print("\n=== exhaustive BFS: is dot0 still reachable (i.e. did the piece stay in the same component)? ===")
seen,nodes=exhaustive(copy.deepcopy(cur_e),cur_o,max_nodes=15000)
print(f"expanded {nodes} nodes, {len(seen)} reachable")
xs=[c[0] for c in seen]; ys=[c[1] for c in seen]
print(f"bbox x=[{min(xs)},{max(xs)}] y=[{min(ys)},{max(ys)}]")
print(f"dot0 cells reachable: {[c in seen for c in d0_now]}")
