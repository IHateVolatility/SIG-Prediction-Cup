"""Figures for the write-up, each in a light and a dark version (GitHub picks one with <picture>).

    uv run python writeup/make_figures.py            # all
    uv run python writeup/make_figures.py fill_map   # one

Reads writeup/data/ (see prep_data.py), writes writeup/figures/<name>-<light|dark>.png.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

HERE = Path(__file__).parent
DATA, OUT = HERE / "data", HERE / "figures"
ME = "nimble-beacon-4953"
START = 100_000

THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e9e8e2",
                  axis="#c3c2b7", series=["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300",
                                          "#6250d6", "#e34948"],
                  pos="#2a78d6", neg="#e34948", mid="#f0efec", band=0.13, other="#c9c8c1"),
    "dark": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781", grid="#2c2c2a",
                 axis="#383835", series=["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300",
                                         "#9085e9", "#e66767"],
                 pos="#3987e5", neg="#e66767", mid="#383835", band=0.22, other="#4a4a46"),
}  # fmt: skip


def style(th):
    plt.rcParams.update({
        "font.family": "Helvetica Neue",
        "font.size": 10.5,
        "figure.facecolor": th["surface"],
        "axes.facecolor": th["surface"],
        "savefig.facecolor": th["surface"],
        "axes.edgecolor": th["axis"],
        "axes.labelcolor": th["ink2"],
        "axes.titlecolor": th["ink"],
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 26,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": th["grid"],
        "grid.linewidth": 0.8,
        "xtick.color": th["ink2"],
        "ytick.color": th["ink2"],
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "xtick.major.pad": 6,
        "ytick.major.pad": 6,
        "legend.frameon": False,
        "legend.labelcolor": th["ink2"],
        "lines.linewidth": 2,
        "lines.solid_capstyle": "round",
    })  # fmt: skip


def subtitle(ax, th, text):
    ax.text(0, 1.02, esc(text), transform=ax.transAxes, color=th["ink2"], fontsize=10.5, va="bottom")


def money(v, _=None):
    a = abs(v)
    s = "−" if v < 0 else ""
    if a >= 1e6:
        return f"{s}${a / 1e6:.2f}M".replace(".00M", "M")
    if a >= 1e3:
        return f"{s}${a / 1e3:.0f}k"
    return f"{s}${a:.0f}"


def esc(text):
    """Matplotlib reads text between two $ as maths; ours are dollars."""
    return text.replace("$", r"\$")


def dt(t):
    return datetime.fromtimestamp(t, UTC)


def utc(day, hh, mm=0):
    """Epoch seconds of a UTC time in Nov 2026 (day of month)."""
    return datetime(2026, 11, day, hh, mm, tzinfo=UTC).timestamp()


def load(name):
    return json.loads((DATA / name).read_text())


def save(fig, name, mode):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}-{mode}.png", dpi=220, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def note(ax, th, xy, text, xytext, ha="left", color=None, data=True):
    ax.annotate(esc(text), xy=xy, xytext=xytext, textcoords="offset points", ha=ha, va="center", fontsize=9.5,
                color=color or th["ink2"], xycoords="data" if data else "axes fraction",
                arrowprops=dict(arrowstyle="-", color=th["muted"], lw=0.8, shrinkA=2, shrinkB=3))  # fmt: skip


# ---------------------------------------------------------------- 1. the whole Cup


def equity_curve(th, mode):
    eq = np.array([[t, e] for t, e, _ in load("equity.json")], dtype=float)
    cash = np.array([[t, c] for t, _, c in load("equity.json") if c is not None], dtype=float)
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3.2, 1], "hspace": 0.12})
    x = [dt(t) for t in eq[:, 0]]
    c = th["series"][0]
    ax.fill_between(x, START, eq[:, 1], color=c, alpha=th["band"], lw=0)
    ax.plot(x, eq[:, 1], color=c, lw=2.2)
    ax.axhline(START, color=th["axis"], lw=1)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.set_ylim(0, eq[:, 1].max() * 1.1)
    ax.set_title(esc("$100k to $1.55M in five weeks"))
    subtitle(ax, th, "Account value with every position at its fair price (Polymarket/Kalshi), Oct 1 – Nov 4 2026")

    def at(t):
        return np.interp(t, eq[:, 0], eq[:, 1])

    oct = lambda d, h=0: datetime(2026, 10, d, h, tzinfo=UTC).timestamp()  # noqa: E731
    pts = [  # (time, text, text position in data coordinates)
        (oct(2, 12), "Opening days: takers swept thin books\ninto our deep orders. +$756k by Oct 3", (oct(5), 470_000)),
        (oct(14), "Three quiet weeks: deep orders,\nunwinds and a lot of research", (oct(9), 1_250_000)),
        (utc(2, 20), "Nov 2: the last sweeps\nbefore the election, +$173k", (oct(23), 1_250_000)),
        (utc(4, 3), "Election night", (oct(27), 1_400_000)),
        (utc(4, 16, 23), "16:23 on the last day: 88k shares\nof RI Senate D bought at 10c", (oct(20), 1_600_000)),
    ]
    for t, text, (tx, ty) in pts:
        ax.scatter([dt(t)], [at(t)], s=30, color=th["surface"], edgecolor=c, lw=1.7, zorder=5)
        ax.annotate(esc(text), xy=(dt(t), at(t)), xytext=(dt(tx), ty), fontsize=9.8, color=th["ink2"], va="center",
                    arrowprops=dict(arrowstyle="-", color=th["muted"], lw=0.8, shrinkA=3, shrinkB=4))  # fmt: skip
    last = eq[-1]
    ax.annotate(money(last[1]), (dt(last[0]), last[1]), xytext=(8, 0), textcoords="offset points",
                color=th["ink"], fontsize=13, weight="bold", va="center")  # fmt: skip

    # cash: the constraint
    bx.fill_between([dt(t) for t in cash[:, 0]], 0, cash[:, 1], color=th["series"][2], alpha=th["band"] + 0.1, lw=0)
    bx.plot([dt(t) for t in cash[:, 0]], cash[:, 1], color=th["series"][2], lw=1.4)
    bx.yaxis.set_major_formatter(mticker.FuncFormatter(money))
    bx.set_ylim(0, None)
    bx.set_ylabel("free cash", color=th["ink2"])
    bx.text(0.005, 0.92, "Cash was what limited us: an order we can't pay for doesn't rest", transform=bx.transAxes,
            color=th["ink2"], fontsize=9.5, va="top")  # fmt: skip
    bx.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, tz=UTC))
    bx.xaxis.set_major_formatter(mdates.DateFormatter("%b %d", tz=UTC))
    bx.set_xlim(dt(eq[0, 0]), dt(eq[-1, 0] + 3600 * 14))
    save(fig, "equity_curve", mode)


def daily(th, mode):
    fills = load("fills.json")
    final = {k: v["fair"] for k, v in load("markets.json").items()}
    day = defaultdict(float)
    for t, ex, side, px, q, role, f0 in fills:
        if final.get(ex) is None:
            continue
        s = 1 if side == "bid" else -1
        day[datetime.fromtimestamp(t, UTC).date()] += s * q * (final[ex] - px)
    days = sorted(day)
    v = np.array([day[d] for d in days])
    fig, ax = plt.subplots(figsize=(12, 4.6))
    cols = [th["pos"] if x >= 0 else th["neg"] for x in v]
    ax.bar(days, v, color=cols, width=0.72, zorder=3)
    ax.axhline(0, color=th["axis"], lw=1, zorder=4)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.set_title("Most of the money came in on five days")
    subtitle(ax, th, "What each day's trades are worth at the final results. Positive: we bought below / sold above.")
    for d, x in zip(days, v, strict=True):
        if abs(x) > 100_000:
            ax.text(d, x + 9000, money(x), ha="center", va="bottom", fontsize=9.5, color=th["ink"], weight="bold")
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.grid(axis="x", visible=False)
    top5 = sum(sorted(v, reverse=True)[:5])
    ax.text(0.5, 0.95, esc(f"best 5 of {len(days)} days: {money(top5)} of {money(v.sum())}"), transform=ax.transAxes,
            ha="center", va="top", color=th["ink2"], fontsize=10.5)  # fmt: skip
    save(fig, "daily", mode)


# ---------------------------------------------------------------- 2. where the edge came from


def edge_buckets(th, mode):
    fills = load("fills.json")
    final = {k: v["fair"] for k, v in load("markets.json").items()}
    buckets = [
        (-1.0, -0.02, "Paid >2c to free cash", "closing positions below fair"),
        (-0.02, 0.02, "Within 2c of fair", "two-sided quotes, unwinds at fair"),
        (0.02, 0.10, "2–10c through fair", "quotes and unwinds"),
        (0.10, 0.30, "10–30c through fair", "deep orders, takes of stale quotes"),
        (0.30, 1.01, "30c+ through fair", "stinks at 0.5–2c / 98–99.5c"),
    ]
    rows = []
    for lo, hi, name, what in buckets:
        val = n = cash = 0.0
        for t, ex, side, px, q, role, f0 in fills:
            if final.get(ex) is None:
                continue
            s = 1 if side == "bid" else -1
            e = s * (f0 - px)
            if lo <= e < hi:
                val += s * q * (final[ex] - px)
                n += 1
                cash += q * (px if s > 0 else 1 - px)
        rows.append((name, what, val, int(n), cash))
    fig, ax = plt.subplots(figsize=(12, 4.8))
    y = np.arange(len(rows))[::-1]
    for yi, (name, what, val, n, cash) in zip(y, rows, strict=True):
        ax.barh(yi, val, color=th["pos"] if val >= 0 else th["neg"], height=0.62, zorder=3)
        ax.text(val + (25_000 if val >= 0 else -25_000), yi + 0.08, money(val), ha="left" if val >= 0 else "right",
                va="center", fontsize=11, weight="bold", color=th["ink"])  # fmt: skip
        ax.text(val + (25_000 if val >= 0 else -25_000), yi - 0.24, esc(f"{n:,} fills · {money(cash)} traded"),
                ha="left" if val >= 0 else "right", va="center", fontsize=9, color=th["ink2"])  # fmt: skip
    ax.set_yticks(y, [f"{r[0]}\n" for r in rows], fontsize=10.5, color=th["ink"])
    for yi, r in zip(y, rows, strict=True):
        ax.text(-0.01, yi - 0.22, r[1], transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=8.8,
                color=th["muted"])  # fmt: skip
    ax.axvline(0, color=th["axis"], lw=1, zorder=4)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.set_xlim(-1.75e6, 2.05e6)
    ax.grid(axis="y", visible=False)
    ax.set_title("The edge was in being far from fair, and freeing cash cost a lot of it")
    subtitle(ax, th, "Every fill by how far through the fair it traded, valued at the final results")
    save(fig, "edge_buckets", mode)


def fill_map(th, mode):
    fills = load("fills.json")
    final = {k: v["fair"] for k, v in load("markets.json").items()}
    xs, ys, ss, cs = [], [], [], []
    for t, ex, side, px, q, role, f0 in fills:
        if final.get(ex) is None or f0 is None:
            continue
        s = 1 if side == "bid" else -1
        xs.append(f0 * 100)
        ys.append(s * (f0 - px) * 100)
        ss.append(q)
        cs.append(s * q * (final[ex] - px))
    xs, ys, ss, cs = map(np.array, (xs, ys, ss, cs))
    order = np.argsort(np.abs(cs))
    fig, ax = plt.subplots(figsize=(12, 7.2))
    cmap = LinearSegmentedColormap.from_list("d", [th["neg"], th["mid"], th["pos"]])
    lim = 30_000
    ax.axhspan(0, 100, color=th["pos"], alpha=0.035, lw=0, zorder=0)
    ax.axhspan(-100, 0, color=th["neg"], alpha=0.035, lw=0, zorder=0)
    sc = ax.scatter(xs[order], ys[order], s=np.clip(ss[order] / 700, 1.5, 260), c=cs[order], cmap=cmap,
                    norm=TwoSlopeNorm(0, -lim, lim), alpha=0.9, lw=0.35, edgecolor=th["surface"], zorder=3)  # fmt: skip
    ax.axhline(0, color=th["axis"], lw=1, zorder=2)
    ax.set_xlim(-2, 102)
    ax.set_ylim(-35, 100)
    ax.set_xlabel("fair value of the market when the fill happened (¢)")
    ax.set_ylabel("edge at the fill (¢ a share, our side)")
    ax.set_title("34,555 fills, and the handful that mattered")
    subtitle(ax, th, "Each dot is one fill: how much better than fair we traded, sized by shares, coloured by its worth at the final result")
    for f0, e, text, xy in [
        (91.5, 91.0, "Oct 1: 43k U.S. House D bought at 0.5c, fair 91c", (52, 97)),
        (55.1, 43.9, "Election night: 41k FL-09 R sold\nto someone at 99c, fair 55c", (63, 46)),
        (76.8, 74.8, "06:09: 41k MS Senate D\nbought at 2c, fair 77c", (50, 79)),
        (99.8, 89.8, "16:23: 88k RI Senate D\nat 9.5–10c, fair 99.8c", (80, 63)),
        (0.3, 89.7, "39k IL Senate R\nsold at 90c, fair 0.3c", (8, 77)),
        (17.0, 16.0, "02:16: 244k AK Senate R\ninto our 1c bid, fair 17c", (20, 40)),
    ]:
        ax.annotate(esc(text), xy=(f0, e), xytext=xy, fontsize=9.5, color=th["ink2"], va="center",
                    arrowprops=dict(arrowstyle="-", color=th["muted"], lw=0.8, shrinkA=3, shrinkB=4))  # fmt: skip
    ax.text(101, 33, "above zero: we traded better than fair", ha="right", va="center", fontsize=9.8, color=th["pos"])
    ax.text(101, -27, "below zero: we paid to get out, mostly to free cash", ha="right", va="center", fontsize=9.8,
            color=th["neg"])  # fmt: skip
    cb = fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.015, format=mticker.FuncFormatter(money), extend="both")
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=th["ink2"], size=0)
    cb.set_label("worth at the final result", color=th["ink2"])
    save(fig, "fill_map", mode)


# ---------------------------------------------------------------- 3. the order book


def book_ladder(th, mode):
    """965 (Montana Senate, Independent wins?) at 12:47 UTC on Nov 4, from the desk: our resting
    asks and everyone else's. Fair 0.1c: the AP had called it for the Republican."""
    asks = [(30.0, 1_700, 0), (90.5, 0, 50_000), (91.0, 30_000, 0), (93.0, 65, 0), (93.5, 1_344_800, 0),
            (98.0, 0, 50_000), (98.5, 4_000, 0), (99.0, 0, 1_000_000)]
    bids = [(6.5, 22_000), (6.0, 539_000), (5.0, 1_000_000), (4.5, 555), (3.5, 2_400), (1.0, 2_600), (0.5, 2_900)]
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ours, others, bidc = th["series"][1], th["other"], th["series"][0]
    def bar(y, n, color, side):
        w = np.log10(max(n, 1)) if n else 0
        ax.barh(y, w * side, height=0.62, color=color, zorder=3)
        return w
    rows = [(p, n, o) for p, n, o in sorted(asks, reverse=True)] + [(p, -n, 0) for p, n in bids]
    ys = np.arange(len(rows))[::-1]
    for y, (p, n, o) in zip(ys, rows, strict=True):
        if n < 0:
            w = bar(y, -n, bidc, -1)
            ax.text(-w - 0.08, y, f"{-n:,}", ha="right", va="center", fontsize=9, color=th["ink2"])
        elif o:
            w = bar(y, o, ours, 1)
            ax.text(w + 0.08, y, f"{o:,}  ours", ha="left", va="center", fontsize=9.5, color=ours, weight="bold")
        else:
            w = bar(y, n, others, 1)
            ax.text(w + 0.08, y, f"{n:,}", ha="left", va="center", fontsize=9, color=th["ink2"])
        ax.text(0, y, f"{p:.1f}¢", ha="center", va="center", fontsize=9.5, color=th["ink"],
                bbox=dict(boxstyle="round,pad=0.25", fc=th["surface"], ec="none"), zorder=5)  # fmt: skip
    ax.set_xlim(-7.5, 8.5)
    ax.set_ylim(ys[-1] - 2.6, ys[0] + 0.8)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.grid(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    split = ys[len(asks)] + 0.5
    ax.axhline(split, color=th["muted"], lw=0.8, ls=(0, (3, 3)))
    ax.text(-7.4, split + 0.35, "asks: selling YES", color=th["ink2"], fontsize=10, va="bottom")
    ax.text(-7.4, split - 0.35, "bids: buying YES", color=th["ink2"], fontsize=10, va="top")
    ax.text(-7.4, ys[-1] - 0.55, "fair value: 0.1¢. The AP had called the race for the Republican.",
            color=th["ink"], fontsize=10.5, weight="bold", va="top")  # fmt: skip
    ax.set_title("What our orders looked like on a decided race")
    subtitle(ax, th, "Book for 'Will the Independent win the Montana Senate?', Nov 4 12:47 UTC (bar length: log of shares)")
    row = {p: y for y, (p, n, o) in zip(ys, rows, strict=True) if n >= 0}
    for p, text in [
        (99.0, "the stink: 1M shares at 99c. Costs $10k of cash, and only if\nsomeone actually buys all of it from us"),
        (98.0, "inner stink, 50k at 98c: fills first if a buyer comes"),
        (90.5, "penny: a tick in front of the 30k bot order at 91c\n(we went as far as 90c)"),
    ]:
        ax.annotate(esc(text), xy=(8.0, row[p]), xytext=(9.3, row[p]), fontsize=9.6, color=th["ink2"], va="center",
                    annotation_clip=False, arrowprops=dict(arrowstyle="-", color=th["muted"], lw=0.8))  # fmt: skip
    ax.text(9.3, row[93.5] - 0.05, "someone else's 1.34M, also selling\nthe longshot", fontsize=9.6, color=th["muted"],
            va="center")  # fmt: skip
    ax.text(-7.4, ys[-1] - 1.1, esc("Who would pay 90c+ for this? Nobody sane. But with thin books, every so often\n"
            "someone sweeps a whole side, and then the order at the front gets the fill."), color=th["ink2"], fontsize=9.8,
            va="top")  # fmt: skip
    save(fig, "book_ladder", mode)


# ---------------------------------------------------------------- 4. election night


def night(th, mode):
    reb = np.array(load("night_rebuilt.json"), dtype=float)
    sim = load("sim_2126.json")
    t0 = sim["t0"]
    base = np.interp(t0, reb[:, 0], reb[:, 1])
    m = reb[:, 0] >= t0
    fig, ax = plt.subplots(figsize=(12.5, 6))
    b = sim["live59"]
    t = np.array(b["t"])
    keep = t <= reb[-1, 0]
    tx = [dt(x) for x in t[keep]]
    ax.fill_between(tx, np.array(b["p10"])[keep], np.array(b["p90"])[keep], color=th["series"][0], alpha=th["band"], lw=0)
    ax.plot(tx, np.array(b["p50"])[keep], color=th["series"][0], lw=1.6)
    h = sim["hold"]
    ax.plot([dt(x) for x in np.array(h["t"])[keep]], np.array(h["p50"])[keep], color=th["muted"], lw=1.3, ls=(0, (4, 3)))
    ax.plot([dt(x) for x in reb[m, 0]], reb[m, 1] - base, color=th["series"][1], lw=2.6, zorder=5)
    ax.axhline(0, color=th["axis"], lw=1)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: ("+" if v > 0 else "") + money(v)))
    ax.set_title("Election night, against the simulation we ran at 21:26")
    subtitle(ax, th, f"Gain since 21:26 UTC at fair value. Blue: {b['n']} simulated nights (median, 10–90%). Dashed: doing nothing.")
    ax.axvline(dt(utc(4, 0)), color=th["grid"], lw=1, zorder=0)
    ax.text(dt(utc(4, 0)), 0.985, " 00:00 UTC: first polls close (7pm ET)", transform=ax.get_xaxis_transform(),
            fontsize=9, color=th["ink2"], va="top")  # fmt: skip

    def at(x):
        return np.interp(x, reb[:, 0], reb[:, 1]) - base

    for x, text, xy in [
        (utc(3, 23, 53), "23:53: someone buys 41k FL-09 R\nfrom our 99c ask (fair 55c)", (utc(3, 21, 35), 150_000)),
        (utc(4, 2, 16), "02:16: 244k AK Senate R sold\ninto our 1c bid (fair 17c)", (utc(4, 0, 20), 420_000)),
        (utc(4, 6, 9), "06:09: MS Senate D dumped into\nour 2c bid, before the race flips", (utc(4, 4, 10), 470_000)),
        (utc(4, 12, 30), "12:30: a bot starts pennying\nour orders in ~100 markets", (utc(4, 9, 40), 175_000)),
        (utc(4, 16, 23), "16:23: 88k RI Senate D\nbought at 10c (fair 99.8c)", (utc(4, 12, 40), 520_000)),
    ]:
        ax.scatter([dt(x)], [at(x)], s=28, color=th["surface"], edgecolor=th["series"][1], lw=1.6, zorder=6)
        ax.annotate(esc(text), xy=(dt(x), at(x)), xytext=(dt(xy[0]), xy[1]), fontsize=9.6, color=th["ink2"], va="center",
                    arrowprops=dict(arrowstyle="-", color=th["muted"], lw=0.8, shrinkA=3, shrinkB=4))  # fmt: skip
    ax.annotate(("+" if at(reb[-1, 0]) > 0 else "") + money(at(reb[-1, 0])), (dt(reb[-1, 0]), at(reb[-1, 0])),
                xytext=(8, 0), textcoords="offset points", fontsize=13, weight="bold", color=th["ink"], va="center")  # fmt: skip
    ax.text(dt(t[keep][-1]), b["p50"][int(keep.sum()) - 1], "  sim median", color=th["series"][0], fontsize=9.5, va="center")
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0, 24, 2), tz=UTC))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=UTC))
    ax.set_xlim(dt(t0), dt(reb[-1, 0] + 2400))
    ax.set_xlabel("UTC, Nov 3 to Nov 4")
    save(fig, "night", mode)


# ---------------------------------------------------------------- 5. the leaderboard


def broken(s, gap=3 * 3600):
    """x, y with a break wherever the series has a hole (the account was off the top 10)."""
    xs, ys = [], []
    for i, (t, v) in enumerate(s):
        if i and t - s[i - 1][0] > gap:
            xs.append(dt((t + s[i - 1][0]) / 2))
            ys.append(np.nan)
        xs.append(dt(t))
        ys.append(v)
    return xs, ys


def dodge(items, min_gap):
    """End labels (y, text, ...) moved apart to at least min_gap, in order."""
    items = sorted(items, key=lambda r: -r[0])
    ys = [r[0] for r in items]
    for i in range(1, len(ys)):
        ys[i] = min(ys[i], ys[i - 1] - min_gap)
    return [(y, *r[1:]) for y, r in zip(ys, items, strict=True)]


def leaderboard(th, mode):
    lb = load("leaderboard.json")
    eq = np.array([[t, e] for t, e, _ in load("equity.json")], dtype=float)
    fig, ax = plt.subplots(figsize=(12.5, 6.4))
    others = [n for n in lb["series"] if n != ME]
    palette = [th["series"][i] for i in (0, 2, 6, 4)]
    me = np.array(lb["series"][ME], dtype=float)
    after = {r[1]: [] for x in lb["after"] for r in x["rows"]}
    for x in lb["after"]:
        for r in x["rows"]:
            after[r[1]].append((x["t"], r[2], r[0]))

    def tail(n, col, lw):
        """The board since the close: a few snapshots, joined to the end of the live series."""
        s = lb["series"][n]
        pts = [(s[-1][0], s[-1][1], s[-1][2]), *after.get(n, [])]
        ax.plot([dt(t) for t, _, _ in pts], [v for _, v, _ in pts], color=col, lw=lw, ls=(0, (3, 1.5)))
        return pts[-1]

    labels = []
    for i, n in enumerate(others):
        s = lb["series"][n]
        col = palette[i] if i < len(palette) else th["other"]
        w = 1.7 if i < len(palette) else 1.1
        ax.plot(*broken([(t, v) for t, v, _ in s]), color=col, lw=w)
        end = tail(n, col, w)
        labels.append((end[1], f"{int(end[2])}. {n[:-5]}", col, "normal"))
    ax.plot(*broken([(t, v) for t, v, _ in lb["series"][ME]]), color=th["series"][1], lw=3, zorder=5)
    me_end = tail(ME, th["series"][1], 3)
    labels.append((me_end[1], f"{int(me_end[2])}. us, on the board", th["series"][1], "bold"))
    m = eq[:, 0] >= me[0, 0]
    t_end = lb["after"][-1]["t"]
    ax.plot([*[dt(x) for x in eq[m, 0]], dt(t_end)], [*(eq[m, 1] - START), eq[-1, 1] - START], color=th["series"][1],
            lw=1.6, ls=(0, (1.5, 2)), zorder=4)  # fmt: skip
    labels.append((eq[-1, 1] - START, "us at fair value (what settles)", th["series"][1], "normal"))
    for y, text, col, w in dodge(labels, 34_000):
        ax.text(dt(t_end + 3 * 3600), y, text, color=col, fontsize=9.6, weight=w, va="center")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.set_title("The top of the leaderboard, and the settlement that follows")
    subtitle(ax, th, f"All-time P&L of the top accounts ({lb['accounts']:,} on the board). Open positions count at a ~4h average price, so the board lags.")
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2, tz=UTC))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d", tz=UTC))
    ax.set_xlim(dt(me[0, 0]), dt(t_end + 86400 * 2.3))
    ax.annotate("steady-ember: one big bet on\nMS Senate D that came in", xy=(dt(utc(4, 9)), 800_000),
                xytext=(dt(utc(1, 0) - 2.5 * 86400), 420_000), fontsize=9.6, color=th["ink2"], va="center",
                arrowprops=dict(arrowstyle="-", color=th["muted"], lw=0.8))  # fmt: skip
    save(fig, "leaderboard", mode)


def standings(th, mode):
    """Estimated final P&L from the reconstructed positions (simulation at Kalshi prices, see the write-up)."""
    s = load("standings.json")
    board = {r[1][:-5]: r[2] for r in load("leaderboard.json")["after"][-1]["rows"]}
    board["us"] = board.pop(ME[:-5])
    fig, ax = plt.subplots(figsize=(12, 3.9))
    ys = list(range(len(s["accounts"]), 0, -1))
    for y, a in zip(ys, s["accounts"], strict=True):
        col = th["series"][a["series"]]
        ax.plot([a["lo"], a["hi"]], [y, y], color=col, lw=9, alpha=0.32, solid_capstyle="round", zorder=2)
        ax.scatter([a["mid"]], [y], s=74, color=col, edgecolor=th["surface"], lw=2, zorder=4)
        ax.scatter([board[a["name"]]], [y], s=74, marker="D", facecolor=th["surface"], edgecolor=col, lw=1.8, zorder=4)
        ax.text(a["mid"], y + 0.3, money(round(a["mid"], -4)), color=th["ink"], fontsize=10.5, weight="bold", ha="center")
        ax.text(board[a["name"]], y + 0.3, money(round(board[a["name"]], -4)), color=th["ink2"], fontsize=9.6, ha="center")
    ax.set_yticks(ys, [a["name"] for a in s["accounts"]])
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.set_xlim(1_240_000, 1_700_000)
    ax.set_ylim(0.5, len(ys) + 0.75)
    ax.set_title("First on the board, probably third at the end")
    subtitle(ax, th, f"Diamond: the board on {s['as_of']}. Dot and bar: estimated final P&L, median and 90% range. Our own book is known, theirs are estimates.")
    save(fig, "standings", mode)


# ---------------------------------------------------------------- 6. per market


def markets(th, mode):
    fills = load("fills.json")
    mk = load("markets.json")
    val = defaultdict(float)
    for t, ex, side, px, q, role, f0 in fills:
        f1 = mk.get(ex, {}).get("fair")
        if f1 is None:
            continue
        s = 1 if side == "bid" else -1
        val[ex] += s * q * (f1 - px)
    items = sorted(val.items(), key=lambda r: -r[1])
    top, bottom = items[:12], items[-3:]
    rest = [v for _, v in items[12:-3]]
    rows = top + [(None, 0.0)] + bottom
    fig, ax = plt.subplots(figsize=(12, 7))
    y = np.arange(len(rows))[::-1]

    def name(ex):
        t = mk[ex]["title"].replace("Will the ", "").replace(" Party win the ", " ").replace("?", "")
        party, race = t.split(" ", 1)
        return f"{race}, {party[0]}"

    for yi, (ex, v) in zip(y, rows, strict=True):
        if ex is None:
            ax.text(2500, yi, esc(f"{len(rest)} more markets: {money(sum(rest))} together, "
                    f"{sum(1 for x in rest if x > 0)} of them positive"), va="center", fontsize=10, color=th["ink2"],
                    style="italic")  # fmt: skip
            continue
        col = th["pos"] if v >= 0 else th["neg"]
        ax.barh(yi, v, color=col, height=0.66, zorder=3)
        ax.text(v + (2500 if v >= 0 else -2500), yi, money(v), va="center", ha="left" if v >= 0 else "right",
                fontsize=9.8, color=th["ink"], weight="bold")  # fmt: skip
    ax.set_yticks(y, ["…" if ex is None else name(ex) for ex, _ in rows], fontsize=10)
    ax.axvline(0, color=th["axis"], lw=1, zorder=4)
    ax.set_xlim(items[-1][1] * 1.3, items[0][1] * 1.12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.grid(axis="y", visible=False)
    ax.set_title(f"{len(items)} markets, and only one cost us real money")
    subtitle(ax, th, "Value of all our trades in each market at the final results. D/R: the Democratic or Republican contract.")
    ax.annotate("we bought 138k MN-01 R at 64.5c at 04:04 on election night\n(fair 75c). The race went the other way.",
                xy=(val["1024"] / 2, y[-1]), xytext=(25_000, y[-1] + 0.9), fontsize=9.5, color=th["ink2"], va="center",
                arrowprops=dict(arrowstyle="-", color=th["muted"], lw=0.8))  # fmt: skip
    save(fig, "markets", mode)


FIGS = [equity_curve, daily, edge_buckets, fill_map, book_ladder, night, leaderboard, standings, markets]

if __name__ == "__main__":
    want = set(sys.argv[1:])
    for mode, th in THEMES.items():
        style(th)
        for f in FIGS:
            if not want or f.__name__ in want:
                f(th, mode)
                print(mode, f.__name__)
