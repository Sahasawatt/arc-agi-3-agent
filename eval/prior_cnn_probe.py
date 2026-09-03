"""$0 probe, iteration 2 of notes/think-research-add-before-draw-2026-09-03.md:
does a StochasticGoose-shaped CNN change-predictor carry signal ACROSS games where the linear probe
(eval/prior_cross_game_probe.py) read <= chance?  Input 16-ch one-hot 64x64 board + 8 action planes
+ 1 click plane; conv 32->64->128 stride 2, global pool, FC -> p(board_changed).  BCE with pos_weight.
Regimes: CROSS-GAME 5-fold by game; SAME-GAME first-half -> second-half (per game, pooled);
controls: shuffled labels under the cross-game regime, train=test upper bound."""
import json, sys, glob, os, re, numpy as np, torch, torch.nn as nn
SEED = int(os.environ.get("SEED", "0")); torch.manual_seed(SEED); np.random.seed(SEED)
S = sys.argv[1]; EPOCHS = int(os.environ.get("EPOCHS", "6"))
fs = sorted(glob.glob(os.path.join(S, "**", "*_p0_events.jsonl"), recursive=True))
def enc(prev, r):
    B = np.array(prev); H, W = B.shape; x = np.zeros((25, 64, 64), np.float32)
    h, w = min(H, 64), min(W, 64)
    x[np.clip(B[:h, :w], 0, 15), np.arange(h)[:, None], np.arange(w)[None, :]] = 1.0
    a = r["action_name"]; x[16 + (int(a[-1]) - 1 if a.startswith("ACTION") else 7)] = 1.0
    m = re.search(r"row=(\d+), col=(\d+)", r.get("action_display", ""))
    if m:
        rr, cc = int(m.group(1)), int(m.group(2))
        if rr < 64 and cc < 64: x[24, rr, cc] = 1.0
    return x
games = {}
for f in fs:
    g = os.path.basename(f)[:4]; prev = None
    for l in open(f, encoding="utf-8"):
        r = json.loads(l); b = r.get("board")
        if r.get("type") == "action" and prev is not None:
            games.setdefault(g, ([], []))
            games[g][0].append(enc(prev, r)); games[g][1].append(1.0 if str(r["board_changed"]) == "True" else 0.0)
        if b is not None: prev = b
games = {g: (np.stack(x), np.array(y, np.float32)) for g, (x, y) in games.items()}
def net():
    return nn.Sequential(nn.Conv2d(25, 32, 3, 2, 1), nn.ReLU(), nn.Conv2d(32, 64, 3, 2, 1), nn.ReLU(),
                         nn.Conv2d(64, 128, 3, 2, 1), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(128, 1))
def fit(X, Y):
    m = net(); pw = torch.tensor((1 - Y.mean()) / max(Y.mean(), 1e-6))
    opt = torch.optim.Adam(m.parameters(), 1e-3); lf = nn.BCEWithLogitsLoss(pos_weight=pw)
    Xt, Yt = torch.tensor(X), torch.tensor(Y)
    for _ in range(EPOCHS):
        p = torch.randperm(len(Yt))
        for i in range(0, len(p), 64):
            idx = p[i:i + 64]; opt.zero_grad(); lf(m(Xt[idx]).squeeze(1), Yt[idx]).backward(); opt.step()
    return m
def score(m, X):
    with torch.no_grad(): return torch.cat([m(torch.tensor(X[i:i + 256])).squeeze(1) for i in range(0, len(X), 256)]).numpy()
def auc(s, y):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1)
    n1 = y.sum(); n0 = len(y) - n1; return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
keys = sorted(games); print("games", len(keys), "transitions", sum(len(v[1]) for v in games.values()), "inert", int(sum((1 - v[1]).sum() for v in games.values())), "epochs", EPOCHS, flush=True)
folds = [keys[i::5] for i in range(5)]
def cross(shuffle=False):
    cs, cy = [], []
    for held in folds:
        Xtr = np.concatenate([games[k][0] for k in keys if k not in held]); Ytr = np.concatenate([games[k][1] for k in keys if k not in held])
        if shuffle: Ytr = np.random.permutation(Ytr)
        m = fit(Xtr, Ytr)
        for k in held: cs.append(score(m, games[k][0])); cy.append(games[k][1])
    return auc(np.concatenate(cs), np.concatenate(cy))
print("CROSS-GAME 5-fold AUC", round(cross(), 3), flush=True)
print("CONTROL shuffled-label cross AUC", round(cross(shuffle=True), 3), flush=True)
Xa = np.concatenate([games[k][0][: len(games[k][1]) // 2] for k in keys]); Ya = np.concatenate([games[k][1][: len(games[k][1]) // 2] for k in keys])
Xb = np.concatenate([games[k][0][len(games[k][1]) // 2:] for k in keys]); Yb = np.concatenate([games[k][1][len(games[k][1]) // 2:] for k in keys])
m = fit(Xa, Ya); print("SAME-GAME first-half -> second-half AUC", round(auc(score(m, Xb), Yb), 3), "n", len(Yb), flush=True)
print("CONTROL train=test (first half) AUC", round(auc(score(m, Xa), Ya), 3), flush=True)
