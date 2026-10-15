#!/usr/bin/env python3
"""Synthetic football (soccer) event-stream generator for MatchMind.

Simulates a 90-minute match as a timed stream of events (passes, shots, tackles,
possession changes, pressure, fouls, cards, goals) with player IDs, team, pitch
coordinates (105x68), timestamps and metadata. Outputs JSONL and/or streams live.
"""
import argparse
import json
import random
import sys
import time
from dataclasses import dataclass, asdict, field
from typing import Optional

PITCH_X, PITCH_Y = 105.0, 68.0
EVENT_TYPES = ["pass", "shot", "tackle", "possession_change", "pressure",
               "foul", "card", "goal", "interception", "clearance"]


def make_squad(team: str, prefix: str):
    positions = (["GK"] + ["DF"] * 4 + ["MF"] * 4 + ["FW"] * 2)
    return [{"player_id": f"{prefix}{i+1:02d}", "team": team,
             "position": positions[i], "shirt": i + 1} for i in range(11)]


def rand_coord():
    return round(random.uniform(0, PITCH_X), 1), round(random.uniform(0, PITCH_Y), 1)


def xg_from_distance(x, y):
    # crude xG: closer to goal (x=105) and central (y=34) => higher
    dist = (((PITCH_X - x) ** 2) + ((PITCH_Y / 2 - y) ** 2)) ** 0.5
    base = max(0.01, min(0.9, 1.4 / (1.0 + dist)))
    return round(base, 3)


@dataclass
class MatchState:
    minute: int = 0
    second: int = 0
    possession_team: str = "HOME"
    score: dict = field(default_factory=lambda: {"HOME": 0, "AWAY": 0})
    seq: int = 0


def gen_events(match_id, seed=None):
    if seed is not None:
        random.seed(seed)
    home = make_squad("HOME", "H")
    away = make_squad("AWAY", "A")
    squads = {"HOME": home, "AWAY": away}
    st = MatchState()
    clock = 0.0  # seconds
    while clock < 90 * 60:
        # advance clock by a realistic gap
        clock += random.uniform(2.0, 9.0)
        st.minute, st.second = int(clock // 60), int(clock % 60)
        st.seq += 1
        team = st.possession_team
        opp = "AWAY" if team == "HOME" else "HOME"
        player = random.choice(squads[team])
        x, y = rand_coord()
        # weighted event choice
        etype = random.choices(
            EVENT_TYPES,
            weights=[55, 6, 9, 10, 8, 4, 1, 0, 4, 3],
            k=1,
        )[0]
        ev = {
            "match_id": match_id,
            "seq": st.seq,
            "minute": st.minute,
            "second": st.second,
            "type": etype,
            "team": team,
            "player_id": player["player_id"],
            "position": player["position"],
            "x": x, "y": y,
            "score": dict(st.score),
        }
        if etype == "pass":
            tx, ty = rand_coord()
            dist = round((((tx - x) ** 2) + ((ty - y) ** 2)) ** 0.5, 1)
            complete = random.random() < max(0.5, 0.95 - dist / 200)
            ev.update({"target_player_id": random.choice(squads[team])["player_id"],
                       "end_x": tx, "end_y": ty, "pass_distance": dist,
                       "pass_difficulty": round(min(1.0, dist / 60), 2),
                       "complete": complete})
            if not complete:
                st.possession_team = opp
        elif etype == "shot":
            xg = xg_from_distance(x, y)
            scored = random.random() < xg
            ev.update({"xg": xg, "on_target": random.random() < 0.45, "goal": scored})
            if scored:
                st.score[team] += 1
                ev["type"] = "goal"
                ev["goal"] = True
                ev["score"] = dict(st.score)
            st.possession_team = opp
        elif etype in ("tackle", "interception", "clearance", "possession_change"):
            st.possession_team = opp
            ev["regained_by"] = opp
        elif etype == "pressure":
            ev["intensity"] = round(random.uniform(0.2, 1.0), 2)
        elif etype == "foul":
            ev["against_player_id"] = random.choice(squads[opp])["player_id"]
        elif etype == "card":
            ev["card"] = random.choices(["yellow", "red"], weights=[9, 1])[0]
        yield ev
    # final whistle
    st.seq += 1
    yield {"match_id": match_id, "seq": st.seq, "minute": 90, "second": 0,
           "type": "full_time", "score": dict(st.score)}


def main(argv=None):
    p = argparse.ArgumentParser(description="MatchMind synthetic event generator")
    p.add_argument("--match-id", default="DEMO-001")
    p.add_argument("--speed", type=float, default=0.0,
                   help="stream speed multiplier (events pace); 0 = dump instantly")
    p.add_argument("--out", default=None, help="write JSONL to this path")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--stream", action="store_true",
                   help="print events to stdout as a live stream")
    args = p.parse_args(argv)

    out_f = open(args.out, "w") if args.out else None
    count = 0
    prev_clock = 0.0
    for ev in gen_events(args.match_id, seed=args.seed):
        line = json.dumps(ev)
        if out_f:
            out_f.write(line + "\n")
        if args.stream:
            print(line, flush=True)
            if args.speed and args.speed > 0:
                cur = ev.get("minute", 0) * 60 + ev.get("second", 0)
                delay = max(0.0, (cur - prev_clock) / args.speed)
                prev_clock = cur
                time.sleep(min(delay, 2.0))
        count += 1
    if out_f:
        out_f.close()
    final = ev.get("score")
    print(f"[MatchMind] generated {count} events for {args.match_id}; "
          f"final score HOME {final['HOME']}-{final['AWAY']} AWAY",
          file=sys.stderr)


if __name__ == "__main__":
    main()
