"""
make_figures.py — generates every chart referenced in the paper
(charts/fig_*.png), either directly from the reference implementations
(dynamics.py, laws.py, entropy.py) or, for the five purely conceptual /
architectural figures that have no underlying numerical model, as clearly
labeled schematic diagrams.

Data-driven (computed from code):
    fig_three_laws, fig_baseline_trajectory, fig_scenario_comparison,
    fig_sensitivity, fig_aeo_intervention, fig_entropy_taxonomy

Illustrative schematics (no underlying dataset — explicitly labeled as such
in-figure, so nobody mistakes a box diagram for a measurement):
    fig_snr_architecture, fig_epistemic_inequality, fig_provenance_stack,
    fig_equilibria
"""

from __future__ import annotations

import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

sys.path.insert(0, ".")
import dynamics as dyn
import laws
import entropy as ent

OUT = "../charts"

# ---------------------------------------------------------------------------
# Shared style
# ---------------------------------------------------------------------------

INK = "#1a1a2e"
SIGNAL = "#2563eb"      # H(t), true entropy / signal
NOISE = "#dc2626"       # s(t), synthetic share
APPARENT = "#94a3b8"    # H_app(t), apparent/volume entropy
VALUE = "#16a34a"       # V(t) / positive interventions
ACCENT = "#d97706"      # secondary accent
GRID = "#e5e7eb"
BG = "#ffffff"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "text.color": INK,
    "axes.edgecolor": "#cbd5e1",
    "axes.labelcolor": INK,
    "xtick.color": "#475569",
    "ytick.color": "#475569",
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.7,
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
})


def savefig(fig, name):
    fig.savefig(f"{OUT}/{name}.png", dpi=190, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {OUT}/{name}.png")


def strip_spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def note(ax, text, y=-0.22):
    ax.text(0.0, y, text, transform=ax.transAxes, fontsize=8.2,
             color="#64748b", style="italic", ha="left", va="top")


# ---------------------------------------------------------------------------
# Figure 1 — fig_three_laws (Section 3), from laws.py
# ---------------------------------------------------------------------------

def fig_three_laws():
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.6))

    # Panel A — Law I: V(s) = k * exp(H_net/H_max)
    ax = axes[0]
    x = np.linspace(0, 1, 200)
    y = [laws.law1_scarcity_value(xi, 1.0, k=1.0) for xi in x]
    ax.plot(x, y, color=SIGNAL, lw=2.2)
    ax.set_xlabel(r"$H_{net}/H_{max}$")
    ax.set_ylabel(r"$V(s)$")
    ax.set_title("Law I — Scarcity-Value", fontsize=11, loc="left")
    strip_spines(ax)
    note(ax, "computed via laws.law1_scarcity_value, k=1.0")

    # Panel B — Law II: SNR(p) = I / (I + N_synth), I fixed at 2 bits
    ax = axes[1]
    n_synth = np.linspace(0, 40, 200)
    y = [laws.law2_snr(2.0, n) for n in n_synth]
    ax.plot(n_synth, y, color=NOISE, lw=2.2)
    ax.set_xlabel(r"$N_{synth}(p)$  (bits)")
    ax.set_ylabel(r"$SNR(p)$")
    ax.set_title("Law II — SNR  (I(p)=2 bits fixed)", fontsize=11, loc="left")
    ax.set_ylim(0, 1.05)
    strip_spines(ax)
    note(ax, "computed via laws.law2_snr")

    # Panel C — Law III: verification premium over time, several lambdas
    ax = axes[2]
    t = np.linspace(0, 8, 200)
    for lam, c, lbl in [(0.2, APPARENT, "λ=0.20"), (0.35, ACCENT, "λ=0.35 (baseline)"), (0.5, NOISE, "λ=0.50")]:
        y = [laws.law3_verification_premium(1.0, lam, ti) for ti in t]
        ax.plot(t, y, lw=2.2, color=c, label=lbl)
    ax.set_xlabel("t  (time since saturation onset)")
    ax.set_ylabel(r"$P(s_{verified}) / P(s_{unverified})$")
    ax.set_title("Law III — Verification Premium", fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    strip_spines(ax)
    note(ax, "computed via laws.law3_verification_premium")

    fig.suptitle("The three laws — reference implementation output (Section 3–4)", fontsize=12.5, y=1.06, x=0.02, ha="left")
    savefig(fig, "fig_three_laws")


# ---------------------------------------------------------------------------
# Figure 2 — fig_baseline_trajectory (Section 5.2), from dynamics.py
# ---------------------------------------------------------------------------

def fig_baseline_trajectory():
    result = dyn.simulate(dyn.SCENARIOS["baseline"])
    checkpoints = [0, 3, 6, 9, 12]
    table = dyn.trajectory_table(result, checkpoints)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.4, 6.4), sharex=True,
                                    gridspec_kw={"height_ratios": [1.4, 1]})

    ax1.plot(result["t"], result["H"], color=SIGNAL, lw=2.2, label=r"$H(t)$ — true entropy")
    ax1.plot(result["t"], result["H_app"], color=APPARENT, lw=2.2, ls="--", label=r"$H_{app}(t)$ — apparent entropy")
    ax1.plot(result["t"], result["s"], color=NOISE, lw=1.8, label=r"$s(t)$ — synthetic share")
    for row in table:
        ax1.scatter([row["t"]], [row["H(t)"]], color=SIGNAL, zorder=5, s=26)
        ax1.scatter([row["t"]], [row["H_app(t)"]], color=APPARENT, zorder=5, s=26)
    ax1.fill_between(result["t"], result["H"], result["H_app"],
                      where=(result["H_app"] >= result["H"]), color=NOISE, alpha=0.06,
                      label="false-maximum-entropy wedge (§5.2)")
    ax1.set_ylabel("entropy (normalized)")
    ax1.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax1.set_title("Baseline trajectory — H(t), H_app(t), s(t)", fontsize=11, loc="left")
    strip_spines(ax1)

    ax2b = ax2.twinx()
    ax2.plot(result["t"], result["SNR_proxy"], color=INK, lw=2.2, label=r"$SNR_{proxy}(t)=H/H_{app}$")
    ax2b.plot(result["t"], result["V"], color=VALUE, lw=2.0, ls=":", label=r"$V(t)$ (right axis)")
    for row in table:
        ax2.scatter([row["t"]], [row["SNR_proxy(t)"]], color=INK, zorder=5, s=26)
    ax2.set_xlabel("t (normalized time)")
    ax2.set_ylabel(r"$SNR_{proxy}(t)$")
    ax2b.set_ylabel(r"$V(t)$", color=VALUE)
    ax2b.tick_params(axis="y", colors=VALUE)
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=8.5, loc="upper right")
    strip_spines(ax2)
    ax2b.spines["top"].set_visible(False)
    note(ax2, "generated by dynamics.simulate(SCENARIOS['baseline']); markers = §5.2 checkpoint table (t=0,3,6,9,12)", y=-0.28)

    fig.tight_layout()
    savefig(fig, "fig_baseline_trajectory")


# ---------------------------------------------------------------------------
# Figure 3 — fig_scenario_comparison (Section 5.3)
# ---------------------------------------------------------------------------

def fig_scenario_comparison():
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    colors = {"baseline": INK, "high_synthetic": NOISE, "strong_provenance": VALUE, "fast_collapse": ACCENT}
    labels = {"baseline": "Baseline", "high_synthetic": "High-synthetic",
              "strong_provenance": "Strong-provenance", "fast_collapse": "Fast-collapse"}
    for name, p in dyn.SCENARIOS.items():
        r = dyn.simulate(p, t_max=12.0)
        ax.plot(r["t"], r["SNR_proxy"], lw=2.3, color=colors[name],
                label=f"{labels[name]}  (SNR_proxy(12)={r['SNR_proxy'][-1]:.3f})")
    ax.set_xlabel("t (normalized time)")
    ax.set_ylabel(r"$SNR_{proxy}(t)$")
    ax.set_title("Scenario comparison — four named parameterizations (§5.3)", fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=8.7, loc="upper right")
    strip_spines(ax)
    note(ax, "generated from dynamics.SCENARIOS via dynamics.simulate")
    fig.tight_layout()
    savefig(fig, "fig_scenario_comparison")


# ---------------------------------------------------------------------------
# Figure 4 — fig_sensitivity (Section 5.4)
# ---------------------------------------------------------------------------

def fig_sensitivity():
    grid = dyn.sensitivity_grid(n=9, t_eval=10.0)
    bsweep = dyn.beta_sweep()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4))

    im = ax1.imshow(grid["SNR_proxy_final"].T, origin="lower", cmap="RdYlBu",
                     extent=[grid["alphas"][0], grid["alphas"][-1], grid["lambdas"][0], grid["lambdas"][-1]],
                     aspect="auto", vmin=0, vmax=grid["SNR_proxy_final"].max())
    cbar = fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
    cbar.set_label(r"$SNR_{proxy}(t{=}10)$", fontsize=9)
    ax1.scatter([0.2], [0.1], color="black", marker="o", s=50, zorder=5)
    ax1.annotate(f"  α=0.2,λ=0.1\n  SNR={grid['SNR_proxy_final'][0,0]:.2f}", (0.2, 0.1),
                 fontsize=8, va="center")
    ax1.scatter([1.0], [1.0], color="black", marker="o", s=50, zorder=5)
    ax1.annotate(f"α=1.0,λ=1.0\nSNR={grid['SNR_proxy_final'][-1,-1]:.3f}  ", (1.0, 1.0),
                 fontsize=8, va="top", ha="right")
    ax1.set_xlabel(r"$\alpha$ (synthetic growth rate)")
    ax1.set_ylabel(r"$\lambda$ (collapse rate)")
    ax1.set_title("9×9 sensitivity grid", fontsize=11, loc="left")

    ax2.plot(bsweep["betas"], bsweep["SNR_proxy_final"], color=VALUE, lw=2.3, marker="o", ms=3.5)
    ax2.set_xlabel(r"$\beta$ (provenance strength)")
    ax2.set_ylabel(r"$SNR_{proxy}(t{=}10)$")
    ax2.set_title(r"β sweep ($\alpha$=0.55, $\lambda$=0.35 fixed)", fontsize=11, loc="left")
    ax2.set_ylim(0, max(0.4, bsweep["SNR_proxy_final"].max() * 1.2))
    strip_spines(ax2)
    note(ax2, "note the shallow slope vs. the α/λ grid at left")

    fig.suptitle("Sensitivity analysis (§5.4) — generated via dynamics.sensitivity_grid / dynamics.beta_sweep",
                 fontsize=11.5, y=1.04, x=0.01, ha="left")
    fig.tight_layout()
    savefig(fig, "fig_sensitivity")


# ---------------------------------------------------------------------------
# Figure 5 — fig_aeo_intervention (Section 5.5)
# ---------------------------------------------------------------------------

def fig_aeo_intervention():
    aeo = dyn.aeo_intervention_scenario()
    interv = aeo["intervention"]
    base = aeo["baseline_no_intervention"]

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(base["t"], base["SNR_proxy"], color=APPARENT, lw=2.0, ls="--", label="No-intervention baseline")
    ax.plot(interv["t"], interv["SNR_proxy"], color=VALUE, lw=2.4, label="AEO intervention at t=5")
    ax.axvline(aeo["t_break"], color=NOISE, lw=1.2, ls=":")
    ax.annotate("β: 1.0→2.2\nh_inject: 0.02→0.06", xy=(aeo["t_break"], 0.6),
                xytext=(aeo["t_break"] + 0.4, 0.75), fontsize=8.3, color=NOISE,
                arrowprops=dict(arrowstyle="->", color=NOISE, lw=1))
    for t_check in [5.0, 7.3, 9.6, 12.0]:
        yi = float(np.interp(t_check, interv["t"], interv["SNR_proxy"]))
        ax.scatter([t_check], [yi], color=VALUE, zorder=5, s=24)
    ax.set_xlabel("t (normalized time)")
    ax.set_ylabel(r"$SNR_{proxy}(t)$")
    ax.set_title("AEO intervention vs. no-intervention counterfactual (§5.5)", fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    strip_spines(ax)
    note(ax, "generated via dynamics.aeo_intervention_scenario — slows decline, does not reverse it")
    fig.tight_layout()
    savefig(fig, "fig_aeo_intervention")


# ---------------------------------------------------------------------------
# Figure 6 — fig_entropy_taxonomy (Section 10.1), from entropy.py
# ---------------------------------------------------------------------------

def fig_entropy_taxonomy():
    # Reproduce the three worked examples exactly as in entropy.py's __main__.
    paraphrase_tokens = [f"variant_{i}" for i in range(50)]
    paraphrase_claims = ["wire_report_X"] * 50
    h_stat_v = ent.h_stat(paraphrase_tokens)
    h_sem_v = ent.h_sem(paraphrase_claims)

    health_claims = [f"claim_{i}" for i in range(20)]
    health_just = ["unsourced_assertion"] * 20
    h_sem2 = ent.h_sem(health_claims)
    h_ep2 = ent.h_ep(health_just)

    apparent_bylines = [f"byline_{i}" for i in range(1000)]
    true_authors = ["content_farm_operator_A"] * 1000
    h_apparent = ent.entropy_from_labels(apparent_bylines)
    h_auth_v = ent.h_auth(true_authors)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))

    pairs = [
        (axes[0], ["H_stat\n(surface form)", "H_sem\n(claim diversity)"], [h_stat_v, h_sem_v],
         "Paraphrase farm:\n50 wordings, 1 claim"),
        (axes[1], ["H_sem\n(claim diversity)", "H_ep\n(justification diversity)"], [h_sem2, h_ep2],
         "Health claims:\n20 claims, 0 evidence"),
        (axes[2], ["apparent\n(byline entropy)", "H_auth\n(true author entropy)"], [h_apparent, h_auth_v],
         "Byline laundering:\n1000 bylines, 1 operator"),
    ]
    for ax, labels, vals, title in pairs:
        bars = ax.bar(labels, vals, color=[APPARENT, NOISE], width=0.55)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.15, f"{v:.2f}", ha="center", fontsize=9)
        ax.set_ylabel("bits")
        ax.set_title(title, fontsize=10, loc="left")
        ax.set_ylim(0, max(vals) * 1.25 + 0.5)
        strip_spines(ax)

    fig.suptitle("Entropy taxonomy — three worked examples (§10.1), computed via entropy.py", fontsize=12, y=1.05, x=0.02, ha="left")
    fig.tight_layout()
    savefig(fig, "fig_entropy_taxonomy")


# ---------------------------------------------------------------------------
# Figure 7 — fig_snr_architecture (Section 6.2) — CONCEPTUAL SCHEMATIC
# ---------------------------------------------------------------------------

def fig_snr_architecture():
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    levels = [
        (0.4, "Level 1 — Document\nSNR_doc = w_scp(1-SCP) + w_ns·NS + w_pv·PV", SIGNAL, 2.6),
        (3.6, "Level 2 — Domain\nSNR_domain = (1/n)Σ SNR_doc(d_i)·w(d_i)", ACCENT, 2.6),
        (6.8, "Level 3 — Global Web\nSNR_web(t) = Σ_D market_share(D,t)·SNR_domain(D,t)", VALUE, 2.6),
    ]
    for x, text, color, w in levels:
        box = FancyBboxPatch((x, 1.6), w, 1.6, boxstyle="round,pad=0.08,rounding_size=0.12",
                              linewidth=1.6, edgecolor=color, facecolor=color + "1A")
        ax.add_patch(box)
        ax.text(x + w / 2, 2.4, text, ha="center", va="center", fontsize=8.6, color=INK)
    for x0, x1 in [(3.0, 3.6), (6.2, 6.8)]:
        ax.annotate("", xy=(x1, 2.4), xytext=(x0, 2.4),
                     arrowprops=dict(arrowstyle="-|>", color="#64748b", lw=1.6))
    ax.text(5.0, 4.4, "Three-level SNR measurement architecture (§6.2)", ha="center", fontsize=12.5, color=INK)
    ax.text(5.0, 0.9, "Illustrative schematic — structure only, not a data output.\nSignals A (SCP), B (NS), C (PV) feed Level 1; see §6.2.",
            ha="center", fontsize=8.3, style="italic", color="#64748b")
    savefig(fig, "fig_snr_architecture")


# ---------------------------------------------------------------------------
# Figure 8 — fig_entropy_taxonomy already covers §10.1; now §12.1 — CONCEPTUAL
# ---------------------------------------------------------------------------

def fig_epistemic_inequality():
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xlabel("positioned to capture the Law III verification premium →", fontsize=9.5)
    ax.set_ylabel("personal / institutional risk in seeking verification →", fontsize=9.5)
    ax.axhline(5, color="#cbd5e1", lw=1)
    ax.axvline(5, color="#cbd5e1", lw=1)

    points = [
        (8.2, 1.8, "Institutionally embedded\nexperts / elites", SIGNAL),
        (2.0, 2.0, "Lay public without\ninstitutional access", APPARENT),
        (7.6, 8.4, "Expert under an\nauthoritarian regime", NOISE),
        (2.4, 7.2, "Global-South ecosystem:\nunder-resourced\n+ exposed", ACCENT),
    ]
    for x, y, label, c in points:
        ax.scatter([x], [y], s=140, color=c, zorder=5, edgecolor="white", linewidth=1.2)
        ax.annotate(label, (x, y), xytext=(0, 14), textcoords="offset points",
                    ha="center", fontsize=8.4, color=INK)

    ax.set_xticks([]); ax.set_yticks([])
    strip_spines(ax)
    ax.spines["left"].set_visible(True)
    ax.spines["bottom"].set_visible(True)
    ax.set_title("Two forms of epistemic inequality (§12.1)", fontsize=12, loc="left")
    note(ax, "Illustrative positioning of archetypes discussed in the text — not measured data.", y=-0.1)
    savefig(fig, "fig_epistemic_inequality")


# ---------------------------------------------------------------------------
# Figure 9 — fig_provenance_stack (Section 13.1) — CONCEPTUAL SCHEMATIC
# ---------------------------------------------------------------------------

def fig_provenance_stack():
    fig, ax = plt.subplots(figsize=(8, 6.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11)
    ax.axis("off")

    layers = [
        ("Layer 5 — Epistemic Value Markets (EVM)", VALUE),
        ("Layer 4 — SNR-Aware Indexing (SAI)", ACCENT),
        ("Layer 3 — Attestation Network (AN)", "#7c3aed"),
        ("Layer 2 — Content Signing Protocol (CSP)", SIGNAL),
        ("Layer 1 — Author Key Registry (AKR)", INK),
    ]
    h = 1.7
    for i, (text, color) in enumerate(layers):
        y = 0.6 + i * (h + 0.25)
        box = FancyBboxPatch((1.0, y), 8.0, h, boxstyle="round,pad=0.06,rounding_size=0.1",
                              linewidth=1.6, edgecolor=color, facecolor=color + "1A")
        ax.add_patch(box)
        ax.text(5.0, y + h / 2, text, ha="center", va="center", fontsize=10, color=INK)
        if i < len(layers) - 1:
            ax.annotate("", xy=(5.0, y + h + 0.25), xytext=(5.0, y + h),
                        arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.4))
    ax.text(5.0, 10.5, "The five-layer provenance stack (§13.1)", ha="center", fontsize=12.5)
    ax.text(5.0, 0.15, "Illustrative dependency diagram — each layer's adoption is contingent on the layer below it (§13.2).",
            ha="center", fontsize=8.3, style="italic", color="#64748b")
    savefig(fig, "fig_provenance_stack")


# ---------------------------------------------------------------------------
# Figure 10 — fig_equilibria (Section 13.4) — CONCEPTUAL SCHEMATIC
# ---------------------------------------------------------------------------

def fig_equilibria():
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    states = [
        (0.6, "E1\nPre-saturation web\n(pre-~2022)", APPARENT),
        (3.9, "E2\nCurrent low-trust\nequilibrium (default trajectory)", NOISE),
        (7.2, "E3\nAuthority Web\n(provenance stack adopted)", VALUE),
    ]
    w = 2.3
    for x, text, color in states:
        box = FancyBboxPatch((x, 1.4), w, 1.8, boxstyle="round,pad=0.08,rounding_size=0.12",
                              linewidth=1.6, edgecolor=color, facecolor=color + "1A")
        ax.add_patch(box)
        ax.text(x + w / 2, 2.3, text, ha="center", va="center", fontsize=9, color=INK)

    ax.annotate("", xy=(3.9, 2.3), xytext=(2.9, 2.3), arrowprops=dict(arrowstyle="-|>", color="#64748b", lw=1.8))
    ax.text(3.4, 2.65, "default drift", ha="center", fontsize=8, color="#64748b")
    ax.annotate("", xy=(7.2, 2.3), xytext=(6.2, 2.3), arrowprops=dict(arrowstyle="-|>", color=VALUE, lw=1.8, linestyle="--"))
    ax.text(6.7, 2.65, "coordination fix\n(§13–14)", ha="center", fontsize=8, color=VALUE)

    ax.text(5.0, 4.3, "Three equilibria of the web's information ecology (§13.4)", ha="center", fontsize=12.5)
    ax.text(5.0, 0.6, "Illustrative — a market-failure / coordination-failure framing, not a physical law (§10.5).",
            ha="center", fontsize=8.3, style="italic", color="#64748b")
    savefig(fig, "fig_equilibria")


if __name__ == "__main__":
    print("Generating figures into", OUT)
    fig_three_laws()
    fig_baseline_trajectory()
    fig_scenario_comparison()
    fig_sensitivity()
    fig_aeo_intervention()
    fig_entropy_taxonomy()
    fig_snr_architecture()
    fig_epistemic_inequality()
    fig_provenance_stack()
    fig_equilibria()
    print("Done.")
