"""Full-corpus variant of eval/prior_cnn_probe.py: boards kept as uint8, one-hot built per batch;
all inert transitions + NEG_PER_POS x as many changed ones sampled per game (AUC is base-rate free)."""
import json, sys, glob, os, re, numpy as np, torch, torch.nn as nn
SEED = int(os.environ.get("SEED", "0")); torch.manual_seed(SEED); rng = np.random.default_rng(SEED)
S = sys.argv[1]; EPOCHS = int(os.environ.get("EPOCHS", "5")); NEG_PER_POS = int(os.environ.get("NEG_PER_POS", "5"))
fs = sorted(glob.glob(os.path.join(S, "**", "*_p0_events.jsonl"), recursive=True))
raw = {}
for f in fs:
    g = os.path.basename(f)[:4]; prev = None
    for l in open(f, encoding="utf-8"):
        r = json.loads(l); b = r.get("board")
        if r.get("type") == "action" and prev is not None:
            B = np.array(prev, dtype=np.uint8); H, W = B.shape; board = np.full((64, 64), 255, np.uint8)
            board[:min(H, 64), :min(W, 64)] = np.clip(B[:64, :64], 0, 15)
            a = r["action_name"]; ai = int(a[-1]) - 1 if a.startswith("ACTION") else 7
            m = re.search(r"row=(\d+), col=(\d+)", r.get("action_display", "")); rr, cc = (int(m.group(1)), int(m.group(2))) if m else (255, 255)
            raw.setdefault(g, []).append((board, ai, rr, cc, 1.0 if str(r["board_changed"]) == "True" else 0.0))
        if b is not None: prev = b
games = {}
tot = 0; inert = 0
for g, rows in raw.items():
    pos = [x for x in rows if x[4] == 0.0]; neg = [x for x in rows if x[4] == 1.0]
    tot += len(rows); inert += len(pos)
    k = min(len(neg), NEG_PER_POS * max(len(pos), 1))
    keep = pos + [neg[i] for i in rng.choice(len(neg), k, replace=False)] if neg else pos
    rng.shuffle(keep)
    games[g] = (np.stack([x[0] for x in keep]), np.array([x[1] for x in keep]), np.array([(x[2], x[3]) for x in keep]), np.array([x[4] for x in keep], np.float32))
print("games", len(games), "transitions", tot, "inert", inert, "sampled", sum(len(v[3]) for v in games.values()), "epochs", EPOCHS, flush=True)
def onehot(boards, acts, clicks):
    n = len(acts); x = torch.zeros((n, 25, 64, 64))
    b = torch.tensor(boards.astype(np.int64)); mask = b < 16
    x[:, :16].scatter_(1, torch.where(mask, b, torch.zeros_like(b)).unsqueeze(1), mask.unsqueeze(1).float())
    for i in range(n):
        x[i, 16 + acts[i]] = 1.0
        if clicks[i][0] < 64 and clicks[i][1] < 64: x[i, 24, clicks[i][0], clicks[i][1]] = 1.0
    return x
def net():
    return nn.Sequential(nn.Conv2d(25, 32, 3, 2, 1), nn.ReLU(), nn.Conv2d(32, 64, 3, 2, 1), nn.ReLU(), nn.Conv2d(64, 128, 3, 2, 1), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(128, 1))
def fit(parts):
    B = np.concatenate([p[0] for p in parts]); A = np.concatenate([p[1] for p in parts]); C = np.concatenate([p[2] for p in parts]); Y = np.concatenate([p[3] for p in parts])
    m = net(); pw = torch.tensor((1 - Y.mean()) / max(Y.mean(), 1e-6)); opt = torch.optim.Adam(m.parameters(), 1e-3); lf = nn.BCEWithLogitsLoss(pos_weight=pw)
    for _ in range(EPOCHS):
        p = np.random.permutation(len(Y))
        for i in range(0, len(p), 128):
            idx = p[i:i + 128]; opt.zero_grad(); lf(m(onehot(B[idx], A[idx], C[idx])).squeeze(1), torch.tensor(Y[idx])).backward(); opt.step()
    return m
def score(m, part):
    B, A, C, Y = part; out = []
    with torch.no_grad():
        for i in range(0, len(Y), 256): out.append(m(onehot(B[i:i + 256], A[i:i + 256], C[i:i + 256])).squeeze(1))
    return torch.cat(out).numpy()
def auc(s, y):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); n1 = y.sum(); n0 = len(y) - n1; return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
keys = sorted(games); folds = [keys[i::5] for i in range(5)]
def cross(shuffle=False, nfold=5):
    cs, cy = [], []
    for held in folds[:nfold]:
        parts = [games[k] for k in keys if k not in held]
        if shuffle: parts = [(p[0], p[1], p[2], rng.permutation(p[3])) for p in parts]
        m = fit(parts)
        for k in held: cs.append(score(m, games[k])); cy.append(games[k][3])
    return auc(np.concatenate(cs), np.concatenate(cy))
print("CROSS-GAME 5-fold AUC", round(cross(), 3), flush=True)
print("CONTROL shuffled-label cross AUC (2 folds)", round(cross(shuffle=True, nfold=2), 3), flush=True)
half = lambda p, first: tuple(a[: len(p[3]) // 2] if first else a[len(p[3]) // 2:] for a in p)
m = fit([half(games[k], True) for k in keys])
Xb = tuple(np.concatenate([half(games[k], False)[i] for k in keys]) for i in range(4))
print("SAME-GAME first-half -> second-half AUC", round(auc(score(m, Xb), Xb[3]), 3), "n", len(Xb[3]), flush=True)
