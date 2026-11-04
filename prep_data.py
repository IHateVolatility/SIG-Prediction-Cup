"""Collect the write-up's data into writeup/data/ (small JSON files, so make_figures.py runs anywhere).

Inputs are the server exports (see the scripts next to this one's use in the write-up notes):
equity samples, every fill with the fair just before it, the leaderboard watcher's snapshots, the
dashboard state at the end, the night rebuilt from fills, and the 21:26 simulation.

    uv run python writeup/prep_data.py <export dir>
"""

import gzip
import json
import sys
from pathlib import Path

import numpy as np

ME = "nimble-beacon-4953"


def main():
    src = Path(sys.argv[1])
    out = Path(__file__).parent / "data"
    out.mkdir(exist_ok=True)
    d = json.load(gzip.open(src / "writeup_data.json.gz"))
    st = json.load(open(src / "state_final.json"))
    markets = {m["id"]: {"title": m["title"], "fair": m["fair"], "pos": m["position"]} for m in st["markets"]}
    (out / "markets.json").write_text(json.dumps(markets))
    (out / "header.json").write_text(json.dumps(st["header"]))

    # equity at fair every 10 minutes; the 02:02-07:29 hole on 11-04 filled from the rebuild
    eq = [[t, e, c] for t, e, p, c, lk in d["equity"] if e is not None]
    reb = json.load(open(Path(__file__).parents[1] / "data/postnight/rebuilt.json"))
    hole = (1793757720, 1793777340)
    eq = [r for r in eq if not hole[0] < r[0] < hole[1]]
    eq += [[t, v, None] for t, v, _ in reb if hole[0] < t < hole[1]]
    eq.sort()
    (out / "equity.json").write_text(json.dumps(eq))
    (out / "night_rebuilt.json").write_text(json.dumps(reb))

    fills = json.load(gzip.open(src / "fillfair.json.gz"))
    (out / "fills.json").write_text(json.dumps(fills))

    # leaderboard: all-time P&L of the accounts that finish in the top 8, plus us
    lb = [x for x in d["leaderboard"] if x["p"] == "all"]
    final = lb[-1]
    names = [r[1] for r in final["top"][:8]]
    if ME not in names:
        names.append(ME)
    series = {n: [] for n in names}
    for x in lb:
        rows = {r[1]: r for r in x["top"]}
        if x["me"]:
            rows[ME] = x["me"]
        for n in names:
            if n in rows:
                series[n].append([x["t"], rows[n][2], rows[n][0]])
    weekly = [[x["t"], x["me"][0], x["me"][2]] for x in d["leaderboard"] if x["p"] == "7d" and x["me"]]
    (out / "leaderboard.json").write_text(
        json.dumps({"series": series, "final": final["top"], "accounts": final["n"], "weekly_rank": weekly})
    )

    # the 21:26 simulation: percentiles of the gain, for the live strategy and doing nothing
    sim = json.loads((Path(__file__).parents[1] / "data/stalesim/paths-2126.json").read_text())
    band = {}
    for strat in ("live59", "hold"):
        runs = [r for r in sim["runs"] if r["strategy"] == strat]
        n = min(len(r["path"]) for r in runs)
        t = [row[0] for row in runs[0]["path"][:n]]
        a = np.array([[row[2] for row in r["path"][:n]] for r in runs]) - sim["value0"]
        band[strat] = {"t": t, "p10": np.percentile(a, 10, 0).tolist(), "p50": np.median(a, 0).tolist(),
                       "p90": np.percentile(a, 90, 0).tolist(), "n": len(runs)}  # fmt: skip
    band["t0"] = sim["t0"]
    (out / "sim_2126.json").write_text(json.dumps(band))
    for f in sorted(out.iterdir()):
        print(f.name, f.stat().st_size)


if __name__ == "__main__":
    main()
