"""ARC-AGI-3 agent with a swappable policy.

    uv run python agent.py --policy random --game ls20 --steps 200
    uv run python agent.py --policy ollama --game ls20 --steps 200 --model qwen2.5:7b

A policy is `f(obs, actions, history) -> (GameAction, data_dict)`.
"""

import argparse
import json
import random
import re
from collections import Counter

import numpy as np
import requests
from arcengine import GameState

import arc_agi
from perception import describe, movement, objects

CHARS = "0123456789abcdef"
OLLAMA = "http://127.0.0.1:11434/api/generate"
STATS = {"fallback": 0}


def grid_text(obs):
    """64x64 int8 frame -> 64 lines of 64 hex chars."""
    g = np.array(obs.frame)[-1]
    return "\n".join("".join(CHARS[v & 0xF] for v in row) for row in g)


def random_policy(obs, actions, history, **_):
    a = random.choice(actions)
    d = {"x": random.randint(0, 63), "y": random.randint(0, 63)} if a.is_complex() else {}
    return a, d


PROMPT = """You are playing an unknown 2D puzzle game. You must infer the rules by acting.

The screen is a 64x64 grid. Each character is one cell's colour (hex 0-f).

{grid}

Available actions: {actions}
{complex_note}
Levels completed so far: {levels}

Recent history (action -> cells that changed):
{history}

Pick the single action most likely to make progress. Prefer actions whose past
effect looked purposeful; if an action never changed anything, try a different one.
Reply with JSON only: {{"action": <number>{coord_note}}}"""


def ollama_policy(obs, actions, history, model="qwen2.5:7b", **_):
    has_complex = any(a.is_complex() for a in actions)
    hist = "\n".join(f"  {a} -> {n} cells changed" for a, _, n in history[-8:]) or "  (none yet)"
    prompt = PROMPT.format(
        grid=grid_text(obs),
        actions=[a.value for a in actions],
        complex_note='Actions marked complex also need "x" and "y" in 0..63.\n' if has_complex else "",
        levels=obs.levels_completed,
        history=hist,
        coord_note=', "x": <0-63>, "y": <0-63>' if has_complex else "",
    )
    r = requests.post(
        OLLAMA,
        json={"model": model, "prompt": prompt, "stream": False, "format": "json",
              "options": {"temperature": 0.7, "num_ctx": 8192}},
        timeout=180,
    )
    r.raise_for_status()
    raw = r.json()["response"]
    try:
        pick = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'"action"\s*:\s*(\d+)', raw)
        pick = {"action": int(m.group(1))} if m else {}

    by_val = {a.value: a for a in actions}
    action = by_val.get(pick.get("action"))
    if action is None:  # model named an action it cannot take
        STATS["fallback"] += 1
        return random_policy(obs, actions, history)
    data = {}
    if action.is_complex():
        data = {"x": int(pick.get("x", 32)) % 64, "y": int(pick.get("y", 32)) % 64}
    return action, data


PROMPT2 = """You are playing an unknown 2D puzzle on a 64x64 grid. Infer the rules by acting.

What is on screen right now (objects, not raw pixels):
{scene}

Available actions: {actions}
{complex_note}Levels completed: {levels}

What your last actions did:
{history}

Reason about which object you control and what the others might be for.
An action that produced "nothing moved" is blocked in that direction right now.
Pick the action most likely to make progress.
Reply with JSON only: {{"action": <number>{coord_note}}}"""


def ollama2_policy(obs, actions, history, model="qwen2.5:7b", **_):
    objs, terrain = objects(obs.frame)
    has_complex = any(a.is_complex() for a in actions)
    hist = "\n".join(f"  action {a}: {'; '.join(ev)}" for a, ev, _ in history[-8:]) or "  (nothing yet)"
    prompt = PROMPT2.format(
        scene=describe(objs, terrain),
        actions=[a.value for a in actions],
        complex_note='Complex actions also need "x" and "y" in 0..63.\n' if has_complex else "",
        levels=obs.levels_completed,
        history=hist,
        coord_note=', "x": <0-63>, "y": <0-63>' if has_complex else "",
    )
    return _ask(prompt, model, obs, actions, history)


def _ask(prompt, model, obs, actions, history):
    r = requests.post(
        OLLAMA,
        json={"model": model, "prompt": prompt, "stream": False, "format": "json",
              "options": {"temperature": 0.7, "num_ctx": 8192}},
        timeout=180,
    )
    r.raise_for_status()
    raw = r.json()["response"]
    try:
        pick = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'"action"\s*:\s*(\d+)', raw)
        pick = {"action": int(m.group(1))} if m else {}

    by_val = {a.value: a for a in actions}
    action = by_val.get(pick.get("action"))
    if action is None:
        STATS["fallback"] += 1
        return random_policy(obs, actions, history)
    data = {}
    if action.is_complex():
        data = {"x": int(pick.get("x", 32)) % 64, "y": int(pick.get("y", 32)) % 64}
    return action, data


POLICIES = {"random": random_policy, "ollama": ollama_policy, "ollama2": ollama2_policy}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--policy", default="random", choices=POLICIES)
    p.add_argument("--game", default="ls20")
    p.add_argument("--steps", type=int, default=100)
    p.add_argument("--model", default="qwen2.5:7b")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    random.seed(args.seed)
    arc = arc_agi.Arcade()
    env = arc.make(args.game)
    if env is None:
        raise SystemExit(f"failed to create env {args.game}")

    policy = POLICIES[args.policy]
    obs = env.reset()
    prev = np.array(obs.frame)[-1]
    prev_objs, _ = objects(obs.frame)
    history, resets, best = [], 0, 0

    for step in range(args.steps):
        action, data = policy(obs, env.action_space, history, model=args.model)
        obs = env.step(action, data=data)
        if obs is None:
            continue
        cur = np.array(obs.frame)[-1]
        cur_objs, _ = objects(obs.frame)
        history.append((action.value, movement(prev_objs, cur_objs), int((cur != prev).sum())))
        prev, prev_objs = cur, cur_objs
        best = max(best, obs.levels_completed)

        if obs.state == GameState.WIN:
            print(f"WIN at step {step}")
            break
        if obs.state == GameState.GAME_OVER:
            resets += 1
            env.reset()

    dead = sum(1 for _, _, n in history if n <= 2)  # <=2 == only the HUD budget bar ticked
    mix = Counter(a for a, _, _ in history)
    print(f"policy={args.policy} game={args.game} steps={len(history)} "
          f"levels={best} resets={resets} no-op_actions={dead}/{len(history)} "
          f"fallback_to_random={STATS['fallback']} action_mix={dict(sorted(mix.items()))}")


if __name__ == "__main__":
    main()
