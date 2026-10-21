"""Figures for the Falcon3-7B sovereign audit report v2.
Evidence encoding used in every figure:
  solid fill  = tier A (script in the release package, numbers from the author's run logs)
  hatched     = tier B (numbers from the author's run logs, script NOT in the package)
Nothing here was re-measured; all values are copied from the author's report.
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch
from matplotlib.lines import Line2D

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#1f2937", "#6b7280", "#e5e7eb"
BLUE, TEAL, ORANGE, RED, GREEN, GREY = "#2563eb", "#0f766e", "#d97706", "#b91c1c", "#15803d", "#9ca3af"

plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"],
    "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 10, "axes.titlelocation": "left",
    "hatch.linewidth": 0.8, "figure.dpi": 100, "savefig.dpi": 200,
})


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- Fig 1
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")

    def box(x, y, w, h, title, sub, fc, ec):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc=fc, ec=ec, lw=1.4))
        ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="top", fontsize=8.6, fontweight="bold", color=INK)
        ax.text(x + w / 2, y + h - 8.6, sub, ha="center", va="top", fontsize=7.2, color=INK, linespacing=1.35)

    def arrow(x1, x2, y):
        ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=11, lw=1.4, color=MUTED))

    y, h, w = 30, 25, 17.5
    xs = [1, 21.5, 42, 62.5, 83]
    box(xs[0], y, w, h, "Client", "query +\ncontext record", "#f3f4f6", GREY)
    box(xs[1], y, w, h, "1  Ingress vault", "regex swap:\nID, IBAN, passport\n-> <PII_TYPE_n>", "#dbeafe", BLUE)
    box(xs[2], y, w, h, "2  Model", "Falcon3-7B-Instruct\nBF16, greedy,\nsees tags only", "#f3f4f6", GREY)
    box(xs[3], y, w, h, "3  Egress gate", "keyword in query\nAND tag in output\n-> fixed refusal", "#dbeafe", BLUE)
    box(xs[4], y, w - 1, h, "4  Rehydrate", "authorised: restore\nelse [REDACTED]", "#dbeafe", BLUE)
    for i in range(4):
        arrow(xs[i] + w + 0.9, xs[i + 1] - 0.9, y + h / 2)

    ax.text(1, 59, "Rule-based containment prototype (what the code does)", fontsize=9.5, fontweight="bold")
    ax.text(1, 56, "Blue = deterministic rule layers around an unmodified model. No activation monitoring is performed.",
            fontsize=7.6, color=MUTED)

    # known gaps
    ax.add_patch(FancyBboxPatch((1, 2), 98, 22, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc="#fffbeb", ec=ORANGE, lw=1.3, ls=(0, (4, 2))))
    ax.text(3, 21.5, "Known gaps (tested locally, no GPU needed)", fontsize=8.4, fontweight="bold", color="#92400e", va="top")
    gaps = [
        "Vault: one notation per type (dashed Emirates ID, upper-case IBAN, no spaces).",
        "Not replaced: IDs without dashes, spaced or lower-case IBAN, names, balances, phones.",
        "Gate keywords hit legitimate queries (\"account fee\") and miss paraphrases (\"national number\").",
        "Gate ignores caller role: an authorised user can be refused. Mask-or-restore does the real work.",
        "A static token blocklist exists in the reference code; no measured run used it.",
    ]
    for i, g in enumerate(gaps):
        ax.text(3.5, 17.4 - i * 3.3, "-  " + g, fontsize=7.4, va="center")
    save(fig, "fig1_architecture.png")


# ---------------------------------------------------------------- Fig 2
def fig_throughput():
    b = [1, 4, 8, 16]
    tp = [46.0, 174.4, 340.1, 649.6]
    itl = [21.7, 22.9, 23.5, 24.6]
    eff = [100.0, 94.8, 92.4, 88.3]
    fig, (a, c) = plt.subplots(1, 2, figsize=(7.2, 3.3), gridspec_kw={"wspace": 0.3, "width_ratios": [1.25, 1]})
    x = list(range(4))
    a.bar(x, tp, width=0.58, color=BLUE, alpha=0.55, hatch="////", edgecolor=BLUE, lw=0.8, zorder=2)
    for xi, v, e in zip(x, tp, eff):
        a.text(xi, v + 14, f"{v:.1f}", ha="center", fontsize=8.6, fontweight="bold")
        a.text(xi, v / 2, f"{e:.0f} %" if xi else "", ha="center", fontsize=7.6, color=INK,
               bbox=dict(fc="white", ec="none", pad=1.2, alpha=0.85))
    a.set_xticks(x); a.set_xticklabels([f"{v}" for v in b]); a.set_xlabel("concurrent sequences (batch)")
    a.set_ylabel("aggregate throughput (tokens/s)"); a.set_ylim(0, 740); a.grid(axis="y", color=GRID, zorder=0)
    a.set_title("Throughput (14.1x at 16x load)")
    c.plot(x, itl, color=ORANGE, marker="o", lw=2)
    for xi, v in zip(x, itl):
        c.text(xi, v + 1.3, f"{v} ms", ha="center", fontsize=8.2, color="#92400e")
    c.set_xticks(x); c.set_xticklabels([f"{v}" for v in b]); c.set_xlabel("concurrent sequences (batch)")
    c.set_ylim(0, 32); c.set_ylabel("inter-token latency (ms)"); c.grid(axis="y", color=GRID)
    c.set_title("Step time (+13 % at 16x load)")
    fig.text(0.0, -0.07, "Tier B. Percentages in the bars = scaling efficiency against batch 1. Flat step time up to batch 16 is typical of a memory-bandwidth-bound decode.\n"
             "Peak VRAM 13.93 to 14.05 GB over the whole range (29 % of the 48 GB partition).", fontsize=7.3, color=MUTED, va="top")
    save(fig, "fig2_throughput.png")


# ---------------------------------------------------------------- Fig 3
def fig_prefill():
    ctx = [1024, 4096, 8192, 32768]
    ttft = [183.60, 387.41, 785.24, 3772.77]
    rate = [c / t * 1000 for c, t in zip(ctx, ttft)]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.3), gridspec_kw={"wspace": 0.32})
    a.plot(ctx, ttft, color=BLUE, marker="o", lw=2)
    for c, t in zip(ctx, ttft):
        a.annotate(f"{t:,.0f} ms", (c, t), textcoords="offset points", xytext=(8, 7) if c == 1024 else (-6, 8), ha="left" if c == 1024 else "right", fontsize=8)
    a.set_xscale("log", base=2); a.set_yscale("log")
    from matplotlib.ticker import FixedLocator, FixedFormatter
    a.yaxis.set_major_locator(FixedLocator([200, 500, 1000, 2000, 4000])); a.yaxis.set_major_formatter(FixedFormatter(["200", "500", "1000", "2000", "4000"])); a.yaxis.set_minor_formatter(FixedFormatter([]))
    a.set_xticks(ctx); a.set_xticklabels(["1k", "4k", "8k", "32k"])
    a.set_xlabel("prompt length (tokens)"); a.set_ylabel("time to first token (ms)")
    a.grid(color=GRID); a.set_title("Prefill latency")
    colors = [ORANGE, BLUE, BLUE, BLUE]
    bars = b.bar(range(4), rate, color=colors, width=0.6, alpha=0.9)
    for i, v in enumerate(rate):
        b.text(i, v + 150, f"{v:,.0f}", ha="center", fontsize=8.5, fontweight="bold") if i else b.text(i, v + 150, f"{v:,.0f}", ha="center", fontsize=8.5, fontweight="bold")
    b.set_xticks(range(4)); b.set_xticklabels(["1k", "4k", "8k", "32k"])
    b.set_xlabel("prompt length (tokens)"); b.set_ylabel("prefill throughput (tokens/s)")
    b.set_ylim(0, 12800); b.grid(axis="y", color=GRID); b.set_axisbelow(True)
    b.set_title("Prefill throughput")
    b.text(0, rate[0] + 1500, "cold start?\nnot tested", ha="center", fontsize=7.4, color="#92400e")
    fig.text(0.0, -0.1, "Tier A. Prompt = one Arabic sentence repeated to length (not statute text). Peak VRAM 14.2 to 22.4 GB from 1k to 32k.\nThe 1k point runs at about half the 4k rate; warm-up used 32 tokens and the cache was cleared before each run.",
             fontsize=7.4, color=MUTED)
    save(fig, "fig3_prefill.png")


# ---------------------------------------------------------------- Fig 4
def fig_pii():
    rows = [
        ("Direct request", "100/100", 100, "B", "96/100", 96, "B"),
        ("\"Maintenance mode\" override", "58/100", 58, "B", "0/100", 0, "B"),
        ("Multi-turn recall (3 turns)", "50/50", 100, "B", "0/50", 0, "A"),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 3.7))
    ypos = [2.4, 1.2, 0.0]
    h = 0.34
    for (lab, ec, ev, et, ac, av, at), y in zip(rows, ypos):
        for off, val, cnt, tier, col in ((h / 1.9, ev, ec, et, BLUE), (-h / 1.9, av, ac, at, TEAL)):
            ax.barh(y + off, val, height=h, color=col, alpha=0.5 if tier == "B" else 0.95,
                    hatch="////" if tier == "B" else None, edgecolor=col, lw=0.8, zorder=2)
            ax.text(val + 1.5, y + off, f"{val} %  ({cnt})", va="center", fontsize=8.2, fontweight="bold")
    ax.set_yticks(ypos); ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlim(0, 128); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xlabel("responses that disclosed the identifier (%)")
    ax.grid(axis="x", color=GRID, zorder=0)
    ax.set_title("Unprotected model: leakage of ID and IBAN from the context")
    ax.text(30, -h / 1.9, "unresolved: a 40-token output budget may cut off a\n15 + 23 digit answer; English scripts not in package", fontsize=7.2,
            color="#92400e", va="center")
    ax.set_ylim(-0.6, 3.0)
    h_ = [Patch(fc=BLUE, alpha=0.5, hatch="////", ec=BLUE, label="English, tier B"),
          Patch(fc=TEAL, alpha=0.5, hatch="////", ec=TEAL, label="Arabic, tier B"),
          Patch(fc=TEAL, alpha=0.95, ec=TEAL, label="Arabic, tier A (script in package)")]
    ax.legend(handles=h_, loc="upper center", ncol=3, frameon=False, fontsize=7.6, bbox_to_anchor=(0.45, -0.17))
    save(fig, "fig4_pii_leakage.png")


# ---------------------------------------------------------------- Fig 5
def fig_ab():
    dom = ["PDPL: processing duties", "Labour Law: notice period", "CBUAE: debt burden cap", "ICP: overstay fine", "DIFC Reg. 10: AI rules"]
    a_state = ["inc", "inc", "ok", "fab", "fab"]
    a_txt = ["generic text,\nno terms", "bullets, no\nlimits", "50 %", "\"14 days\",\nno fine", "\"12 Dec 2009\""]
    b_state = ["ok", "inc", "ok", "ok", "inc"]
    a_lat = [1793.4, 1528.0, 1180.4, 355.4, 291.3]
    b_lat = [1547.1, 1546.7, 1261.7, 1478.3, 1545.6]
    colmap = {"ok": GREEN, "inc": ORANGE, "fab": RED}
    fig = plt.figure(figsize=(7.4, 3.9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.55, 1.55, 1.45], wspace=0.12)
    axA, axB, axL = fig.add_subplot(gs[0]), fig.add_subplot(gs[1], sharey=None), fig.add_subplot(gs[2])
    n = len(dom)
    for ax in (axA, axB):
        ax.set_xlim(0, 1); ax.set_ylim(-0.6, n - 0.4); ax.invert_yaxis(); ax.axis("off")
    axA.set_title("A: zero-shot", loc="center"); axB.set_title("B: with statute chunk", loc="center")
    for i in range(n):
        axA.add_patch(FancyBboxPatch((0.05, i - 0.36), 0.9, 0.72, boxstyle="round,pad=0.01,rounding_size=0.06",
                                     fc=colmap[a_state[i]], alpha=0.14, ec=colmap[a_state[i]], lw=1.2))
        axA.text(0.5, i, a_txt[i], ha="center", va="center", fontsize=7.6, color=INK)
        axB.add_patch(FancyBboxPatch((0.05, i - 0.36), 0.9, 0.72, boxstyle="round,pad=0.01,rounding_size=0.06",
                                     fc=(GREEN if b_state[i] == "ok" else RED), alpha=0.14, ec=(GREEN if b_state[i] == "ok" else RED), lw=1.2))
        axB.text(0.5, i, "at least one\nexpected term" if b_state[i] == "ok" else "no expected\nterm found", ha="center", va="center", fontsize=7.6)
        axA.text(-0.04, i, dom[i], ha="right", va="center", fontsize=8.2)
    axL.set_ylim(-0.6, n - 0.4); axL.invert_yaxis()
    yy = list(range(n))
    axL.barh([y - 0.18 for y in yy], a_lat, height=0.32, color=GREY, label="A")
    axL.barh([y + 0.18 for y in yy], b_lat, height=0.32, color=BLUE, alpha=0.8, label="B")
    axL.set_yticks([]); axL.set_xlim(0, 2200); axL.set_xlabel("latency (ms)")
    axL.set_title("Latency", loc="center"); axL.grid(axis="x", color=GRID); axL.set_axisbelow(True)
    axL.legend(frameon=False, fontsize=7.5, loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.2))
    for s in ("left",):
        axL.spines[s].set_visible(False)
    leg = [Patch(fc=RED, alpha=0.3, ec=RED, label="fabricated figure/date, or no expected term in B"),
           Patch(fc=ORANGE, alpha=0.3, ec=ORANGE, label="not passed under strict rule"),
           Patch(fc=GREEN, alpha=0.3, ec=GREEN, label="passed")]
    fig.legend(handles=leg, loc="lower left", ncol=3, frameon=False, fontsize=7.6, bbox_to_anchor=(0.0, -0.07))
    fig.text(0.0, -0.17, "Tier A. Scoring is asymmetric in the script: A needs ALL expected terms, B needs ANY one. Orange cells are therefore not reliable;\n"
             "red cells in A rest on logged outputs; red cells in B failed even the lenient rule.\n"
             "Latency tracks answer length (tokens not logged), not quality.",
             fontsize=7.3, color=MUTED, va="top")
    save(fig, "fig5_grounding_ab.png")


# ---------------------------------------------------------------- Fig 6
def fig_dialect():
    lab = ["Pure phonetic Arabizi", "Chat slang (no dots)", "Levantine (Shami)", "Khaleeji", "Gaf/Chaf script", "Arabizi with 3/5/7"]
    acc = [100.0, 100.0, 100.0, 100.0, 83.3, 83.3]
    lat = [214.2, 266.1, 303.6, 378.3, 465.6, 493.2]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.2), gridspec_kw={"wspace": 0.08, "width_ratios": [1.2, 1]}, sharey=True)
    y = list(range(len(lab)))
    cols = [BLUE if v == 100 else ORANGE for v in acc]
    a.barh(y, acc, color=cols, alpha=0.55, hatch="////", edgecolor=cols, lw=0.8, height=0.58, zorder=2)
    for yi, v in zip(y, acc):
        a.text(v - 2, yi, f"{v:.1f} %", ha="right", va="center", fontsize=8.4, fontweight="bold", color=INK, bbox=dict(fc="white", ec="none", pad=1.2, alpha=0.9))
    a.set_xlim(0, 112); a.set_xticks([0, 50, 100]); a.set_xlabel("fact extracted correctly (%)")
    a.set_yticks(y); a.set_yticklabels(lab); a.invert_yaxis(); a.grid(axis="x", color=GRID, zorder=0)
    a.set_title("Accuracy")
    b.barh(y, lat, color=GREY, height=0.58, zorder=2)
    for yi, v in zip(y, lat):
        b.text(v + 8, yi, f"{v:.0f} ms", va="center", fontsize=8.2)
    b.set_xlim(0, 640); b.set_xlabel("mean latency (ms)"); b.grid(axis="x", color=GRID, zorder=0)
    b.set_title("Latency"); b.spines["left"].set_visible(False); b.tick_params(left=False)
    fig.text(0.0, -0.06, "Tier B. Per-archetype sample is tiny (script: 6 cases; reported intervals imply 12): one miss moves accuracy by 8 to 17 points.\n"
             "The latency gap for digit Arabizi fits subword fragmentation, but token counts were not logged: hypothesis, check in Appendix B.",
             fontsize=7.3, color=MUTED, va="top")
    save(fig, "fig6_dialect.png")


# ---------------------------------------------------------------- Fig 7 (evidence overview)
def fig_evidence():
    rows = [
        ("Decode throughput, VRAM (batch 1-16)", "B"),
        ("Prefill 1k-32k", "A"),
        ("Single-turn leakage, EN + AR (N=100 each)", "B"),
        ("Maintenance override, EN + AR", "B"),
        ("Multi-turn recall, Arabic", "A"),
        ("Multi-turn recall, English", "B"),
        ("Document-injection, Arabic", "A"),
        ("Document-injection, English", "B"),
        ("Grounding A/B on 5 statutes", "A"),
        ("Dialect and orthography matrix", "A/B"),
        ("Determinism (20 repeats, 1 prompt)", "A"),
        ("Hardened pipeline: 0 % leakage, 0 % FPR", "B"),
        ("Hardened pipeline: single demo record", "A"),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    ax.set_xlim(0, 10); ax.set_ylim(-0.7, len(rows) - 0.3); ax.invert_yaxis(); ax.axis("off")
    for i, (t, tier) in enumerate(rows):
        ax.text(0, i, t, va="center", fontsize=8.6)
        if tier == "A":
            ax.add_patch(FancyBboxPatch((7.2, i - 0.28), 2.5, 0.56, boxstyle="round,pad=0.02,rounding_size=0.12", fc=BLUE, ec=BLUE, alpha=0.9))
            ax.text(8.45, i, "A  script in package", ha="center", va="center", fontsize=7.6, color="white", fontweight="bold")
        elif tier == "B":
            ax.add_patch(FancyBboxPatch((7.2, i - 0.28), 2.5, 0.56, boxstyle="round,pad=0.02,rounding_size=0.12", fc="white", ec=ORANGE, lw=1.4, hatch="////"))
            ax.text(8.45, i, "B  logs only", ha="center", va="center", fontsize=7.6, color="#92400e", fontweight="bold",
                    bbox=dict(fc="white", ec="none", pad=0.8))
        else:
            ax.add_patch(FancyBboxPatch((7.2, i - 0.28), 2.5, 0.56, boxstyle="round,pad=0.02,rounding_size=0.12", fc="#e5e7eb", ec=MUTED, lw=1.2))
            ax.text(8.45, i, "A and B mixed", ha="center", va="center", fontsize=7.6, color=INK, fontweight="bold")
    ax.set_title("Where each result comes from", loc="left")
    ax.text(0, len(rows) - 0.1, "Neither tier was re-run for this revision. Tier only says whether a reader can regenerate the number from the release.",
            fontsize=7.4, color=MUTED, va="top")
    save(fig, "fig0_evidence.png")


for f in (fig_evidence, fig_architecture, fig_throughput, fig_prefill, fig_pii, fig_ab, fig_dialect):
    f()
print("figures written to", OUT)
