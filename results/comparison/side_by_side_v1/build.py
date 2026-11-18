"""Side-by-side tables and figures for #63 from the frozen selected 50/50 index; offline, no API calls.

Run from the repository root: python results/comparison/side_by_side_v1/build.py
"""
import csv, hashlib, json, math
from pathlib import Path
from statistics import pstdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).parent
SRC = {"scores": Path("results/scoring/final_index_v1/scores.json"),
       "trials": Path("results/scoring/final_index_v1/trials.json"),
       "inputs": Path("results/scoring/final_index_v1/inputs.json"),
       "difficulty": Path("results/difficulty/designed_final_v27/task_scores.json")}
DS = ["tau2", "synthetic"]
NAME = {"tau2": "τ²-bench", "synthetic": "Synthetic"}
COLOR = {"tau2": "#2878A5", "synthetic": "#C56635"}  # repo palette from coverage/plot_coverage.py; passes dataviz validator
INK, MUTED, GRID = "#1d2327", "#52616b", "#e6e8ea"
TRIAL_OWNER = {0.7: "Zayd", 0.6: "Ronnit", 0.5: "Divya", 0.4: "Sana", 0.3: "Mila"}
plt.rcParams.update({"font.size": 11, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": INK, "svg.hashsalt": "63", "figure.facecolor": "white"})

load = lambda k: json.loads(SRC[k].read_text())
scores, trials, inputs, diff = load("scores"), load("trials")["rows"], load("inputs"), load("difficulty")
sel = {r["dataset"]: r for r in scores["rows"]}

# Frozen handoff values (#63 description, Nov 15). Fail loudly if any source drifts.
assert diff["release_protocol"] == "designed_difficulty_v1.1_required_path"
assert scores["coverage_weight"] == scores["difficulty_weight"] == 0.5
assert sel["tau2"]["combined_index_0_100"] == 79.66917948727153 and sel["synthetic"]["combined_index_0_100"] == 75.85227439335101
assert sel["tau2"]["coverage_contribution_0_100"] == 47.59184135777513 and sel["synthetic"]["coverage_contribution_0_100"] == 43.97727439335101
for ds in DS:
    r, d = sel[ds], diff["datasets"][ds]
    assert d["mean"] == {"tau2": 64.15467625899281, "synthetic": 63.75}[ds]  # FINAL v1.1, not 65.35/64.30
    assert d["n_scored"] == d["n_total"] and math.isclose(r["difficulty_normalized"] * 100, d["mean"], abs_tol=1e-9)
    assert math.isclose(r["coverage_contribution_0_100"] + r["difficulty_contribution_0_100"], r["combined_index_0_100"], abs_tol=1e-12)
    assert math.isclose(r["coverage"], inputs["datasets"][ds]["coverage"], abs_tol=1e-15)
assert len(trials) == 10

# ---------- tables ----------
def write(name, rows):
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

tasks = {ds: [t["score"] for t in diff["tasks"] if t["dataset"] == ds] for ds in DS}
dims = {ds: {k: np.mean([t["dimensions"][k] for t in diff["tasks"] if t["dataset"] == ds]) for k in diff["tasks"][0]["dimensions"]} for ds in DS}
dataset_rows = []
for ds in DS:
    i, d, r = inputs["datasets"][ds], diff["datasets"][ds], sel[ds]
    dataset_rows.append({
        "dataset": ds, "n_tasks": i["n_tasks"], "difficulty_scored": f"{d['n_scored']}/{d['n_total']}", "n_coverage_groups": i["n_groups"],
        "combined_index_50_50": r["combined_index_0_100"], "coverage_contribution": r["coverage_contribution_0_100"],
        "difficulty_contribution": r["difficulty_contribution_0_100"], "coverage_C_0_100": 100 * i["coverage"],
        "workflow_completeness_A_0_100": 100 * i["catalog_coverage"], "workflows_represented": f"{i['represented']}/{i['declared']}",
        "mean_group_entropy_E_0_100": 100 * i["mean_group_entropy"], "singleton_workflows": i["singleton_workflows"],
        "designed_difficulty_D_0_100": d["mean"], "difficulty_median": d["median"], "difficulty_q1": d["q1"], "difficulty_q3": d["q3"],
        "difficulty_min": d["min"], "difficulty_max": d["max"], "difficulty_population_sd": d["population_stddev"],
        **{f"mean_{k}_0_4": v for k, v in dims[ds].items()}})
write("dataset_comparison.csv", dataset_rows)

group_rows = []
for g in sorted(inputs["groups"], key=lambda g: (DS.index(g["dataset"]), g["group"])):
    d = diff["domains"][f"{g['dataset']}/{g['group']}"]
    assert d["n_total"] == d["n_scored"] == g["tasks"]
    group_rows.append({"dataset": g["dataset"], "group": g["group"], "tasks": g["tasks"],
        "workflows_represented": g["represented"], "workflows_declared": g["declared"], "workflow_completeness": g["catalog_coverage"],
        "normalized_entropy": g["entropy"], "singleton_workflows": g["singleton_workflows"], "difficulty_mean": d["mean"],
        "difficulty_median": d["median"], "difficulty_min": d["min"], "difficulty_max": d["max"], "difficulty_population_sd": d["population_stddev"]})
write("group_comparison.csv", group_rows)

sens_rows = []
for w in sorted({r["coverage_weight"] for r in trials}, reverse=True):
    q = {r["dataset"]: r["combined_index_0_100"] for r in trials if r["coverage_weight"] == w}
    sens_rows.append({"coverage_weight": w, "difficulty_weight": round(1 - w, 10), "reviewer": TRIAL_OWNER[w], "selected": w == 0.5,
                      "tau2_index": q["tau2"], "synthetic_index": q["synthetic"], "gap_tau2_minus_synthetic": q["tau2"] - q["synthetic"],
                      "higher": "tau2" if q["tau2"] > q["synthetic"] else "synthetic"})
write("sensitivity.csv", sens_rows)

gap = sel["tau2"]["combined_index_0_100"] - sel["synthetic"]["combined_index_0_100"]
gap_cov = sel["tau2"]["coverage_contribution_0_100"] - sel["synthetic"]["coverage_contribution_0_100"]
gap_diff = gap - gap_cov

# ---------- figures ----------
def style(ax, xmax=100, xlabel=None):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(GRID); ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, xmax); ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
    if xlabel: ax.set_xlabel(xlabel, color=MUTED)

def header(fig, title, subtitle):
    fig.text(0.04, 0.955, title, fontsize=22, weight="bold", color=INK, va="top")
    fig.text(0.04, 0.895, subtitle, fontsize=12, color=MUTED, va="top")

def footer(fig, lines, y=0.075):
    for k, line in enumerate(lines): fig.text(0.04, y - 0.03 * k, line, fontsize=10, color=MUTED)

def save(fig, stem):
    fig.savefig(OUT / f"{stem}.png", dpi=150, metadata={"Software": None})
    fig.savefig(OUT / f"{stem}.svg", metadata={"Date": None, "Creator": None}); plt.close(fig)

def bar_label(ax, y, x, text, **kw):
    ax.text(x + 1, y, text, va="center", fontsize=10, color=INK, **kw)

# 1. Overall index and components
fig = plt.figure(figsize=(14, 8.4))
header(fig, "Side-by-side: combined index, Coverage and Difficulty",
       "Selected reporting convention Q = 100 × (0.5 Coverage + 0.5 designed Difficulty) • relative index, not validated dataset quality")
for k, ds in enumerate(DS):
    x = 0.04 + 0.47 * k
    fig.text(x, 0.80, f"{NAME[ds]}   {sel[ds]['combined_index_0_100']:.2f} / 100", fontsize=24, weight="bold", color=COLOR[ds], va="top")
    i, d = inputs["datasets"][ds], diff["datasets"][ds]
    fig.text(x, 0.735, f"Coverage {100*i['coverage']:.2f} • Difficulty {d['mean']:.2f} • {d['n_scored']}/{d['n_total']} tasks scored • "
             f"{i['represented']}/{i['declared']} workflows", fontsize=11, color=MUTED, va="top")

ax = fig.add_axes([0.20, 0.17, 0.33, 0.47])
rows = [("Combined index (50/50)", lambda ds: sel[ds]["combined_index_0_100"]),
        ("Coverage C", lambda ds: 100 * inputs["datasets"][ds]["coverage"]),
        ("C part: workflow completeness A", lambda ds: 100 * inputs["datasets"][ds]["catalog_coverage"]),
        ("C part: workflow balance E", lambda ds: 100 * inputs["datasets"][ds]["mean_group_entropy"]),
        ("Designed difficulty D", lambda ds: diff["datasets"][ds]["mean"])]
h = 0.36
for j, (label, f) in enumerate(rows):
    for k, ds in enumerate(DS):
        y = j + (k - 0.5) * (h + 0.04)
        ax.barh(y, f(ds), height=h, color=COLOR[ds], label=NAME[ds] if j == 0 else None)
        bar_label(ax, y, f(ds), f"{f(ds):.2f}")
ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.invert_yaxis()
style(ax, 110, "Score / 100"); ax.set_xticks(range(0, 101, 25))
ax.set_title("Components (0–100)", loc="left", fontsize=13, color=INK, pad=10)
ax.legend(loc="lower right", frameon=False, bbox_to_anchor=(1.0, 1.0), ncol=2)

ax = fig.add_axes([0.62, 0.30, 0.34, 0.30])
for k, ds in enumerate(DS):
    c, dd = sel[ds]["coverage_contribution_0_100"], sel[ds]["difficulty_contribution_0_100"]
    ax.barh(k, c, height=0.55, color=COLOR[ds], edgecolor="white", lw=2)
    ax.barh(k, dd, left=c, height=0.55, color="white", edgecolor=COLOR[ds], hatch="///", lw=1.5)
    ax.text(c / 2, k, f"Coverage {c:.2f}", ha="center", va="center", color="white", fontsize=10, weight="bold")
    ax.text(c + dd / 2, k, f"Difficulty {dd:.2f}", ha="center", va="center", color=INK, fontsize=10,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
    bar_label(ax, k, c + dd, f"= {c + dd:.2f}", weight="bold")
ax.set_yticks(range(2), [NAME[ds] for ds in DS]); ax.invert_yaxis()
style(ax, 100, "Contribution to combined index (points)")
ax.set_title("What each combined index is made of", loc="left", fontsize=13, color=INK, pad=10)
fig.text(0.62, 0.17, f"Gap {gap:.2f} points = {gap_cov:.2f} from Coverage + {gap_diff:.2f} from Difficulty\n"
         f"≈{100*gap_cov/gap:.0f}% of the gap comes from Coverage.", fontsize=11, color=INK)
footer(fig, ["Coverage and Difficulty are scored separately; catalogs differ between datasets, so Coverage is within each dataset's own declared scope.",
             "Difficulty is an LLM-designed complexity rating (five 20% dimensions), not agent failure. Contributions are rounded separately and may differ from totals by 0.01."], y=0.06)
save(fig, "overall_comparison")

# 2. Coverage by group
fig = plt.figure(figsize=(14, 8.6))
header(fig, "Coverage by group: completeness and balance",
       "Each group is scored against its own declared workflow catalog • telecom conditions and Vendi are separate diagnostics")
gl = [f"{NAME[r['dataset']]}: {r['group'].replace('_', ' ')}" for r in group_rows]
for k, (key, title, fmt) in enumerate([("workflow_completeness", "Workflow completeness (represented / declared)", None),
                                       ("normalized_entropy", "Workflow balance (normalized entropy)", None)]):
    ax = fig.add_axes([0.30 + 0.36 * k, 0.17, 0.27, 0.62])
    for j, r in enumerate(group_rows):
        v = 100 * r[key]
        ax.barh(j, v, height=0.6, color=COLOR[r["dataset"]])
        bar_label(ax, j, v, f"{r['workflows_represented']}/{r['workflows_declared']}" if k == 0 else f"{v:.1f}")
    ax.set_yticks(range(len(group_rows)), gl if k == 0 else [""] * len(group_rows)); ax.invert_yaxis()
    style(ax, 115, "Score / 100"); ax.set_xticks(range(0, 101, 25))
    ax.set_title(title, loc="left", fontsize=13, color=INK, pad=10)
    ax.axhline(2.5, color=GRID, lw=1)
footer(fig, [f"Dataset A pools workflows (τ² {inputs['datasets']['tau2']['represented']}/{inputs['datasets']['tau2']['declared']}, "
             f"synthetic {inputs['datasets']['synthetic']['represented']}/{inputs['datasets']['synthetic']['declared']}); dataset E averages groups equally "
             f"(τ² {100*inputs['datasets']['tau2']['mean_group_entropy']:.1f}, synthetic {100*inputs['datasets']['synthetic']['mean_group_entropy']:.1f}).",
             f"Synthetic groups are small (6–13 tasks) and {inputs['datasets']['synthetic']['singleton_workflows']} of its represented workflows have only one task; "
             "τ² has 3 groups of 50–114 tasks. Catalogs are not directly comparable."])
save(fig, "coverage_groups")

# 3. Difficulty spread and domains
fig = plt.figure(figsize=(14, 8.4))
header(fig, "Designed difficulty: spread and domains",
       "FINAL v1.1 • equal-task means • five dimensions weighted 20% each • ranges are across tasks, not confidence intervals")
ax = fig.add_axes([0.13, 0.20, 0.36, 0.55])
rng = np.random.default_rng(63)
for k, ds in enumerate(DS):
    d, s = diff["datasets"][ds], np.array(tasks[ds])
    ax.scatter(s, k + rng.uniform(-0.18, 0.18, len(s)), s=14, color=COLOR[ds], alpha=0.35, lw=0)
    ax.plot([d["q1"], d["q3"]], [k - 0.32] * 2, color=INK, lw=3, solid_capstyle="butt")
    ax.plot([d["mean"]] * 2, [k - 0.40, k - 0.24], color=INK, lw=2)
    ax.text(d["mean"], k - 0.44, f"mean {d['mean']:.2f}", ha="center", va="bottom", fontsize=10, color=INK)
    ax.text(0, k + 0.36, f"{d['n_scored']}/{d['n_total']} scored • median {d['median']:.0f} • IQR {d['q1']:.0f}–{d['q3']:.0f} • "
            f"range {d['min']}–{d['max']} • SD {d['population_stddev']:.1f}", fontsize=9.5, color=MUTED, va="center")
ax.set_yticks(range(2), [NAME[ds] for ds in DS]); ax.set_ylim(1.6, -0.75)
style(ax, 100, "Task designed difficulty / 100"); ax.set_xticks(range(0, 101, 25))
ax.set_title("Every task (dots); black bar = middle 50%, tick = mean", loc="left", fontsize=13, color=INK, pad=10)

ax = fig.add_axes([0.66, 0.20, 0.24, 0.55])
for j, r in enumerate(group_rows):
    ax.plot([r["difficulty_min"], r["difficulty_max"]], [j, j], color=COLOR[r["dataset"]], lw=2, alpha=0.45)
    ax.scatter(r["difficulty_mean"], j, s=60, color=COLOR[r["dataset"]], edgecolor="white", lw=2, zorder=3)
    ax.text(101, j, f"{r['difficulty_mean']:.1f}  n={r['tasks']}", va="center", fontsize=9.5, color=INK)
ax.set_yticks(range(len(group_rows)), [g.replace("Synthetic: ", "").replace("τ²-bench: ", "τ² ") for g in gl], fontsize=9.5)
ax.invert_yaxis(); ax.axhline(2.5, color=GRID, lw=1)
style(ax, 100, "Designed difficulty / 100"); ax.set_xticks(range(0, 101, 25))
ax.set_title("Group mean (dot) and task range (line)", loc="left", fontsize=13, color=INK, pad=10)
footer(fig, [f"Dataset means differ by {diff['datasets']['tau2']['mean'] - diff['datasets']['synthetic']['mean']:.2f} points; τ² is more spread out "
             f"(SD {diff['datasets']['tau2']['population_stddev']:.1f} vs {diff['datasets']['synthetic']['population_stddev']:.1f}). Equal scores would also be valid.",
             "Higher means more complex designed work, not agent failure or better quality. Original-protocol means (65.35/64.30) are superseded and not used."])
save(fig, "difficulty_distribution")

# 4. Weight sensitivity
fig = plt.figure(figsize=(14, 7.6))
header(fig, "Weight sensitivity: all five reviewed settings",
       "Selected 50/50 is a project reporting convention; the other settings stay visible • five policies, not independent samples")
ax = fig.add_axes([0.08, 0.20, 0.62, 0.58])
ws = [r["coverage_weight"] for r in sens_rows][::-1]
for ds in DS:
    qs = [r[f"{ds}_index"] for r in sens_rows][::-1]
    ax.plot(ws, qs, color=COLOR[ds], lw=2, marker="o", ms=8, mec="white", mew=2, label=NAME[ds])
    ax.text(0.71, qs[-1], f"{NAME[ds]}", color=INK, va="center", fontsize=11, weight="bold")
    for w, q in zip(ws, qs): ax.text(w, q + (1.1 if ds == "tau2" else -1.1), f"{q:.2f}", ha="center",
                                     va="bottom" if ds == "tau2" else "top", fontsize=9.5, color=INK,
                                     bbox=dict(facecolor="white", edgecolor="none", pad=1))
ax.axvline(0.5, color=MUTED, lw=1, ls=(0, (3, 3))); ax.text(0.5, 88.6, "selected 50/50", ha="center", fontsize=10, color=MUTED, bbox=dict(facecolor="white", edgecolor="none", pad=2))
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True); ax.set_ylim(66, 90); ax.set_xlim(0.27, 0.78)
ax.set_xticks(ws, [f"{int(w*100)}/{int(round((1-w)*100))}\n{TRIAL_OWNER[w]}" for w in ws])
ax.set_xlabel("Coverage / Difficulty weight (reviewer)", color=MUTED); ax.set_ylabel("Combined index / 100", color=MUTED)
ax.legend(frameon=False, loc="upper left")
tx = 0.75
fig.text(tx, 0.76, "Gap (τ² − synthetic)", fontsize=13, weight="bold", color=INK, va="top")
for k, r in enumerate(sens_rows[::-1]):
    fig.text(tx, 0.70 - 0.045 * k, f"{int(r['coverage_weight']*100)}/{int(round(r['difficulty_weight']*100))}   {r['gap_tau2_minus_synthetic']:.2f} pts"
             + ("   ← selected" if r["selected"] else ""), fontsize=11, color=INK, family="DejaVu Sans Mono")
fig.text(tx, 0.42, "Ordering never changes: τ² is higher on\nboth Coverage and Difficulty, so it leads\nat every weighting by arithmetic. That is\nnot evidence the index is valid.",
         fontsize=10.5, color=MUTED, va="top")
footer(fig, ["Both scores rise with Coverage weight because each dataset's Coverage score is above its Difficulty score; this reflects the weights, not better data."], y=0.05)
save(fig, "weight_sensitivity")

(OUT / "provenance.json").write_text(json.dumps({"api_calls": 0, "selected_convention": "results/scoring/final_index_v1 (50/50)",
    "sources": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in SRC.values()},
    "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "matplotlib": matplotlib.__version__}, indent=2) + "\n")
print(f"gap {gap:.4f} = coverage {gap_cov:.4f} + difficulty {gap_diff:.4f} ({100*gap_cov/gap:.1f}% coverage)")
