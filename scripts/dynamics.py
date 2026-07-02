"""
dynamics.py — The Dynamic Model (Section 5).

Implements the coupled ODE system of Section 5.1:

    ds/dt     = alpha * s * (1 - s) - beta * h_inject * s
    dH/dt     = -lambda * s * H + mu * (1 - s) * (H_max - H)
    dH_app/dt = nu * (1 - 0.5*s) - 0.3 * lambda * s * H_app

with V(t) recovered from Law I using H_app (apparent, not true, entropy),
and SNR_proxy(t) = H(t) / H_app(t).

This is, in the paper's own words, "a minimal mechanism-bearing skeleton,
not a fitted empirical model" (Section 5, Section 5.6) — parameters are
illustrative. Calibration against real SNR_web(t) measurements is listed
as Appendix C, Item 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.integrate import odeint


# ---------------------------------------------------------------------------
# Parameters and state
# ---------------------------------------------------------------------------

@dataclass
class ModelParams:
    """Parameters of the Section 5.1 ODE system."""
    alpha: float = 0.55      # intrinsic growth rate of synthetic content share
    beta: float = 1.0        # provenance/verification infrastructure strength
    lam: float = 0.35        # model collapse rate (lambda)
    mu: float = 0.05         # human-content entropy replenishment rate
    h_inject: float = 0.02   # constant rate of fresh human-data injection
    nu: float = 0.08         # raw content volume growth rate
    h_max: float = 1.0       # theoretical maximum (true) entropy, H(0) = H_max
    k: float = 1.0           # Law I baseline value constant (V(0) = k*e^1 ~= 2.72, Section 5.2)


@dataclass
class InitialState:
    s0: float = 0.05
    H0: float = 1.0
    Happ0: float = 1.0


def _rhs(state: Sequence[float], t: float, p: ModelParams) -> list[float]:
    """Right-hand side of the coupled ODE system."""
    s, H, H_app = state

    ds_dt = p.alpha * s * (1 - s) - p.beta * p.h_inject * s
    dH_dt = -p.lam * s * H + p.mu * (1 - s) * (p.h_max - H)
    dHapp_dt = p.nu * (1 - 0.5 * s) - 0.3 * p.lam * s * H_app

    return [ds_dt, dH_dt, dHapp_dt]


def simulate(
    params: ModelParams,
    init: InitialState = InitialState(),
    t_max: float = 12.0,
    n_points: int = 121,
) -> dict:
    """
    Integrate the ODE system from t=0 to t=t_max.

    Returns a dict of numpy arrays: t, s, H, H_app, V, SNR_proxy.
    """
    t = np.linspace(0.0, t_max, n_points)
    y0 = [init.s0, init.H0, init.Happ0]

    sol = odeint(_rhs, y0, t, args=(params,))
    s, H, H_app = sol[:, 0], sol[:, 1], sol[:, 2]

    V = params.k * np.exp(H_app / params.h_max)
    SNR_proxy = np.divide(H, H_app, out=np.zeros_like(H), where=H_app > 1e-9)

    return {"t": t, "s": s, "H": H, "H_app": H_app, "V": V, "SNR_proxy": SNR_proxy}


def trajectory_table(result: dict, checkpoints: Sequence[float]) -> list[dict]:
    """
    Interpolate a simulate() result onto specific checkpoint times and
    return rows shaped like the Section 5.2 table.
    """
    rows = []
    for tc in checkpoints:
        row = {
            "t": tc,
            "s(t)": float(np.interp(tc, result["t"], result["s"])),
            "H(t)": float(np.interp(tc, result["t"], result["H"])),
            "H_app(t)": float(np.interp(tc, result["t"], result["H_app"])),
            "V(t)": float(np.interp(tc, result["t"], result["V"])),
            "SNR_proxy(t)": float(np.interp(tc, result["t"], result["SNR_proxy"])),
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Section 5.4 — Epistemic half-life
# ---------------------------------------------------------------------------

def epistemic_half_life(params: ModelParams, init: InitialState = InitialState(),
                         t_max: float = 60.0, n_points: int = 6001) -> float:
    """
    tau_1/2: first time at which H(t) falls below 0.5 * H_max.

    Returns float('inf') if H(t) never crosses the threshold within t_max
    (caller should increase t_max in that case).
    """
    result = simulate(params, init, t_max=t_max, n_points=n_points)
    threshold = 0.5 * params.h_max
    below = np.where(result["H"] <= threshold)[0]
    if len(below) == 0:
        return float("inf")
    idx = below[0]
    if idx == 0:
        return float(result["t"][0])
    t0, t1 = result["t"][idx - 1], result["t"][idx]
    H0, H1 = result["H"][idx - 1], result["H"][idx]
    if H1 == H0:
        return float(t1)
    frac = (threshold - H0) / (H1 - H0)
    return float(t0 + frac * (t1 - t0))


# ---------------------------------------------------------------------------
# Section 5.3 — Named scenarios
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, ModelParams] = {
    "baseline":          ModelParams(alpha=0.55, beta=1.0, lam=0.35, mu=0.05, h_inject=0.02, nu=0.08),
    "high_synthetic":    ModelParams(alpha=0.85, beta=0.6, lam=0.55, mu=0.03, h_inject=0.01, nu=0.08),
    "strong_provenance": ModelParams(alpha=0.55, beta=2.2, lam=0.35, mu=0.05, h_inject=0.06, nu=0.08),
    "fast_collapse":     ModelParams(alpha=0.55, beta=1.0, lam=0.90, mu=0.02, h_inject=0.02, nu=0.08),
}


def run_all_scenarios(t_max: float = 12.0) -> dict[str, dict]:
    """Run every named scenario in SCENARIOS and return their results."""
    return {name: simulate(p, t_max=t_max) for name, p in SCENARIOS.items()}


# ---------------------------------------------------------------------------
# Section 5.4 — Sensitivity sweep over (alpha, lambda)
# ---------------------------------------------------------------------------

def sensitivity_grid(
    alpha_range=(0.2, 1.0), lam_range=(0.1, 1.0), n=9, t_eval: float = 10.0
) -> dict:
    """
    Sweep alpha and lambda over an n x n grid (other params held at baseline),
    recording final SNR_proxy(t_eval) and the epistemic half-life for each
    combination. Mirrors Section 5.4.
    """
    alphas = np.linspace(*alpha_range, n)
    lambdas = np.linspace(*lam_range, n)
    snr_grid = np.zeros((n, n))
    halflife_grid = np.zeros((n, n))

    base = ModelParams()
    for i, a in enumerate(alphas):
        for j, l in enumerate(lambdas):
            p = ModelParams(alpha=a, beta=base.beta, lam=l, mu=base.mu,
                             h_inject=base.h_inject, nu=base.nu)
            result = simulate(p, t_max=t_eval, n_points=201)
            snr_grid[i, j] = result["SNR_proxy"][-1]
            halflife_grid[i, j] = epistemic_half_life(p)

    return {
        "alphas": alphas,
        "lambdas": lambdas,
        "SNR_proxy_final": snr_grid,
        "epistemic_half_life": halflife_grid,
    }


def beta_sweep(beta_range=(0.0, 3.0), n=16, t_eval: float = 10.0,
                alpha: float = 0.55, lam: float = 0.35) -> dict:
    """Sweep beta (provenance strength) holding alpha, lambda fixed."""
    betas = np.linspace(*beta_range, n)
    base = ModelParams()
    snr_final = []
    for b in betas:
        p = ModelParams(alpha=alpha, beta=b, lam=lam, mu=base.mu,
                         h_inject=base.h_inject, nu=base.nu)
        result = simulate(p, t_max=t_eval, n_points=201)
        snr_final.append(result["SNR_proxy"][-1])
    return {"betas": betas, "SNR_proxy_final": np.array(snr_final)}


# ---------------------------------------------------------------------------
# Section 5.5 — AEO intervention scenario (discontinuous parameter break)
# ---------------------------------------------------------------------------

def aeo_intervention_scenario(
    t_break: float = 5.0,
    t_max: float = 12.0,
    pre: ModelParams = ModelParams(),
    beta_post: float = 2.2,
    h_inject_post: float = 0.06,
    n_points_per_phase: int = 200,
) -> dict:
    """
    Run the baseline trajectory to t_break, then discontinuously increase
    beta and h_inject at t_break (a stylized AEO/provenance-stack rollout,
    Section 13) and continue to t_max.

    Returns the concatenated trajectory plus the pre/post ModelParams used,
    and a `baseline_no_intervention` trajectory over the same horizon for
    comparison.
    """
    phase1 = simulate(pre, t_max=t_break, n_points=n_points_per_phase)
    state_at_break = InitialState(
        s0=phase1["s"][-1], H0=phase1["H"][-1], Happ0=phase1["H_app"][-1]
    )

    post = ModelParams(
        alpha=pre.alpha, beta=beta_post, lam=pre.lam, mu=pre.mu,
        h_inject=h_inject_post, nu=pre.nu, h_max=pre.h_max, k=pre.k,
    )
    phase2 = simulate(post, init=state_at_break, t_max=t_max - t_break,
                       n_points=n_points_per_phase)
    phase2_t_shifted = phase2["t"] + t_break

    combined = {
        "t": np.concatenate([phase1["t"], phase2_t_shifted[1:]]),
        "s": np.concatenate([phase1["s"], phase2["s"][1:]]),
        "H": np.concatenate([phase1["H"], phase2["H"][1:]]),
        "H_app": np.concatenate([phase1["H_app"], phase2["H_app"][1:]]),
        "V": np.concatenate([phase1["V"], phase2["V"][1:]]),
        "SNR_proxy": np.concatenate([phase1["SNR_proxy"], phase2["SNR_proxy"][1:]]),
    }

    baseline_full = simulate(pre, t_max=t_max, n_points=2 * n_points_per_phase)

    return {
        "intervention": combined,
        "baseline_no_intervention": baseline_full,
        "t_break": t_break,
        "pre_params": pre,
        "post_params": post,
    }


if __name__ == "__main__":
    baseline = simulate(SCENARIOS["baseline"])
    table = trajectory_table(baseline, checkpoints=[0, 3, 6, 9, 12])
    print("Section 5.2 — Baseline trajectory")
    print(f"{'t':>5} {'s(t)':>8} {'H(t)':>8} {'H_app(t)':>10} {'V(t)':>8} {'SNR_proxy(t)':>14}")
    for row in table:
        print(f"{row['t']:>5.1f} {row['s(t)']:>8.3f} {row['H(t)']:>8.3f} "
              f"{row['H_app(t)']:>10.3f} {row['V(t)']:>8.2f} {row['SNR_proxy(t)']:>14.3f}")

    print("\nSection 5.3 — Scenario comparison (SNR_proxy at t=12)")
    for name, p in SCENARIOS.items():
        result = simulate(p, t_max=12.0)
        print(f"  {name:20s} SNR_proxy(12) = {result['SNR_proxy'][-1]:.3f}")

    print("\nSection 5.4 — Sensitivity grid extremes")
    grid = sensitivity_grid(n=9, t_eval=10.0)
    print("  alpha=0.2, lambda=0.1 -> SNR_proxy(10) =",
          round(float(grid["SNR_proxy_final"][0, 0]), 3))
    print("  alpha=1.0, lambda=1.0 -> SNR_proxy(10) =",
          round(float(grid["SNR_proxy_final"][-1, -1]), 3))

    print("\nSection 5.5 — AEO intervention scenario")
    aeo = aeo_intervention_scenario()
    interv = aeo["intervention"]
    base_only = aeo["baseline_no_intervention"]
    for t_check in [5.0, 7.3, 9.6, 12.0]:
        snr_i = float(np.interp(t_check, interv["t"], interv["SNR_proxy"]))
        snr_b = float(np.interp(t_check, base_only["t"], base_only["SNR_proxy"]))
        print(f"  t={t_check:>4.1f}  intervention SNR_proxy={snr_i:.3f}   "
              f"no-intervention SNR_proxy={snr_b:.3f}")
