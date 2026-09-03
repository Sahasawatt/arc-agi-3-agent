"""$0 probe: does a (prev_board, action) -> board_changed predictor carry signal ACROSS games?
numpy logistic regression; features = action one-hot(7) + 5x5 color patch one-hot at mouse coord (400)
+ global color histogram(16). Leave-one-game-out AUC vs within-game (first half -> second half)."""
import json,sys,glob,os,re,numpy as np
S=sys.argv[1]; fs=sorted(glob.glob(os.path.join(S,"**","*_p0_events.jsonl"),recursive=True))
def feat(prev,r):
    a=r["action_name"]; x=np.zeros(8+400+16)
    x[int(a[-1])-1 if a.startswith("ACTION") else 7]=1
    B=np.array(prev)
    h=np.bincount(B.ravel(),minlength=16)[:16]/B.size; x[408:424]=h
    m=re.search(r"row=(\d+), col=(\d+)",r.get("action_display",""))
    if m:
        rr,cc=int(m.group(1)),int(m.group(2))
        for i,dr in enumerate(range(-2,3)):
            for j,dc in enumerate(range(-2,3)):
                y,z=rr+dr,cc+dc
                if 0<=y<B.shape[0] and 0<=z<B.shape[1]:
                    x[8+(i*5+j)*16+min(int(B[y,z]),15)]=1
    return x
games={}
for f in fs:
    g=os.path.basename(f)[:4]; prev=None; X=[];Y=[]
    for l in open(f,encoding="utf-8"):
        r=json.loads(l); b=r.get("board")
        if r.get("type")=="action" and prev is not None:
            X.append(feat(prev,r)); Y.append(1.0 if str(r["board_changed"])=="True" else 0.0)
        if b is not None: prev=b
    if X:
        if g in games: games[g]=(np.vstack([games[g][0],np.array(X)]),np.concatenate([games[g][1],np.array(Y)]))
        else: games[g]=(np.array(X),np.array(Y))
def fit(X,Y,it=400,lr=0.5,l2=1e-3):
    w=np.zeros(X.shape[1]); b=0.0; pw=(1-Y.mean())/max(Y.mean(),1e-6)
    for _ in range(it):
        p=1/(1+np.exp(-(X@w+b))); g=(p-Y)*np.where(Y==1,1.0,pw); w-=lr*(X.T@g/len(Y)+l2*w); b-=lr*g.mean()
    return w,b
def auc(s,y):
    if y.min()==y.max(): return float("nan")
    o=np.argsort(s); r=np.empty(len(s)); r[o]=np.arange(1,len(s)+1)
    n1=y.sum(); n0=len(y)-n1; return (r[y==1].sum()-n1*(n1+1)/2)/(n1*n0)
print("games",len(games),"transitions",sum(len(v[1]) for v in games.values()),"inert",int(sum((1-v[1]).sum() for v in games.values())))
# cross-game
cs=[];cy=[]
for g,(Xt,Yt) in games.items():
    Xtr=np.vstack([v[0] for k,v in games.items() if k!=g]); Ytr=np.concatenate([v[1] for k,v in games.items() if k!=g])
    w,b=fit(Xtr,Ytr); cs.append(Xt@w+b); cy.append(Yt)
cs=np.concatenate(cs); cy=np.concatenate(cy); print("CROSS-GAME leave-one-out pooled AUC",round(auc(cs,cy),3))
# within-game: first half -> second half (games with >=4 inert in test half)
ws=[];wy=[]
for g,(X,Y) in games.items():
    h=len(Y)//2
    if h<10 or (1-Y[h:]).sum()<2 or (1-Y[:h]).sum()<1: continue
    w,b=fit(X[:h],Y[:h]); ws.append(X[h:]@w+b); wy.append(Y[h:])
ws=np.concatenate(ws); wy=np.concatenate(wy); print("WITHIN-GAME half->half pooled AUC",round(auc(ws,wy),3),"n",len(wy))
# controls
rng=np.random.default_rng(0); print("CONTROL shuffled-label cross AUC",round(auc(cs,rng.permutation(cy)),3))
Xa=np.vstack([v[0] for v in games.values()]); Ya=np.concatenate([v[1] for v in games.values()]); w,b=fit(Xa,Ya); print("CONTROL train=test AUC (upper bound)",round(auc(Xa@w+b,Ya),3))
