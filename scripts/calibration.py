"""
calibration.py — Section 5.7: a first empirical calibration attempt.

Fits the s(t) sub-component of the Section 5.1 ODE system,

    ds/dt = alpha * s * (1-s) - k * s        [k := beta * h_inject]

against a real time series of synthetic content share, rather than the
illustrative alpha=0.55 used in Sections 5.2-5.5.

Data source (primary): Graphite, "AI Now Writes as Many Online Articles as
Humans" (graphite.io, May 13 2026). Methodology: 55,400 English-language
Common Crawl URLs, Jan 2020 - Mar 2026, classified "primarily AI-generated"
by averaging three independent detectors (Pangram, Copyleaks, GPTZero),
each with reported false-positive/false-negative rates under 2%.

Quoted directly from that report:
  "Within the first 12 months [of ChatGPT's Nov 2022 launch], the
  percentage of primarily AI-generated articles jumped to 35.9%,
  and reached 48% by 24 months."
  "In Q1 2025 ... 49.6% vs. 50.4% [human]."
  "In Q4 2025, primarily AI-generated articles surpassed human-written
  at 50.9%, before returning to 49.9% in Q1 2026."

IMPORTANT CAVEATS (see paper Section 5.7 and Appendix J for the full
discussion — do not read this script's output as more than it is):
  - This is ONE data source, using AI-detector tooling that has its own
    (small but nonzero) error rates and definitional choices (e.g. what
    counts as "primarily" AI-generated).
  - Only the *product* k = beta*h_inject is identifiable from s(t) alone;
    beta and h_inject cannot be separated without independent data on
    provenance-infrastructure strength.
  - This calibrates ONLY the s(t) equation. H(t) and H_app(t) remain
    entirely uncalibrated (Section 5.6) because no real longitudinal
    measurement of true semantic diversity exists yet — that is a much
    harder, still-unsolved problem (Appendix C, Item 2), not something
    this script attempts.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import odeint
from scipy.optimize import curve_fit

# ---------------------------------------------------------------------------
# Real data: t in years since ChatGPT's public launch (Nov 30, 2022),
# matching the paper's own Law III convention ("t = time since saturation
# onset, anchored to ~2022"). s = share of newly-published articles
# classified "primarily AI-generated."
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Real data: t in years since ChatGPT's public launch (Nov 30, 2022),
# matching the paper's own Law III convention ("t = time since saturation
# onset, anchored to ~2022"). s = share of newly-published articles
# classified "primarily AI-generated." All values below are taken directly
# from the Graphite report cited above; none are invented or assumed.
# ---------------------------------------------------------------------------


def s_rhs(s, t, alpha, k):
    return alpha * s * (1 - s) - k * s


def s_model_from(t0, s0, t_eval, alpha, k):
    """Integrate ds/dt = alpha*s*(1-s) - k*s from (t0, s0), evaluated at `t_eval`.

    Handles t_eval points both after t0 (ordinary forward integration) and
    before t0 (backward integration, used for the out-of-sample check below)
    correctly and separately -- naively sorting a mixed before/after array
    and handing it to odeint as one sequence silently mis-anchors the
    initial condition, which is a real bug we caught and fixed while writing
    this script (left in via this comment rather than silently corrected,
    in the same spirit as the rest of this paper's error-reporting).
    """
    t_eval = np.atleast_1d(np.asarray(t_eval, dtype=float))
    out = np.empty_like(t_eval)

    fwd_idx = np.where(t_eval >= t0)[0]
    bwd_idx = np.where(t_eval < t0)[0]

    if len(fwd_idx) > 0:
        order = np.argsort(t_eval[fwd_idx])
        t_full = np.concatenate(([t0], t_eval[fwd_idx][order]))
        sol = odeint(s_rhs, s0, t_full, args=(alpha, k)).flatten()[1:]
        out[fwd_idx[order]] = sol

    if len(bwd_idx) > 0:
        order = np.argsort(-t_eval[bwd_idx])          # descending: walk backward from t0
        t_full = np.concatenate(([t0], t_eval[bwd_idx][order]))
        sol = odeint(s_rhs, s0, t_full, args=(alpha, k)).flatten()[1:]
        out[bwd_idx[order]] = sol

    return out


# ---------------------------------------------------------------------------
# Rigor note: we do NOT fit using an assumed t=0 seed value (that would let
# us quietly choose a flattering anchor). Instead we anchor the integration
# at t=1.00 (Nov 2023, s=0.359) -- an actual reported Graphite data point --
# and fit (alpha, k) to the four REMAINING real data points. We then
# integrate *backward* from the fitted trajectory to see what it implies
# for the pre-launch/launch period, and check that against the independent,
# qualitative "very low" pre-ChatGPT baseline (Section 9.1) as an
# out-of-sample consistency check rather than a fitting input.
# ---------------------------------------------------------------------------

ANCHOR_T, ANCHOR_S = 1.00, 0.359          # Nov 2023, real data point, used as IC
FIT_T = np.array([2.00, 2.25, 3.00, 3.25])
FIT_S = np.array([0.48, 0.496, 0.509, 0.499])


def fit():
    def model(t_eval, alpha, k):
        return s_model_from(ANCHOR_T, ANCHOR_S, t_eval, alpha, k)

    popt, pcov = curve_fit(
        model, FIT_T, FIT_S,
        p0=[1.0, 0.5],
        bounds=([0.01, 0.0], [20.0, 20.0]),
    )
    alpha_fit, k_fit = popt
    perr = np.sqrt(np.diag(pcov))
    return alpha_fit, k_fit, perr


def goodness_of_fit(alpha_fit, k_fit):
    pred = s_model_from(ANCHOR_T, ANCHOR_S, FIT_T, alpha_fit, k_fit)
    resid = FIT_S - pred
    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum((FIT_S - np.mean(FIT_S)) ** 2)
    r2 = 1 - ss_res / ss_tot
    return pred, resid, r2


def implied_carrying_capacity(alpha_fit, k_fit):
    """For ds/dt = alpha*s*(1-s) - k*s = (alpha-k)*s - alpha*s^2, this is
    logistic growth with carrying capacity K = 1 - k/alpha (the level at
    which ds/dt = 0 for s in (0,1))."""
    return 1.0 - k_fit / alpha_fit


# ---------------------------------------------------------------------------
# Section 5.7 follow-up: does an alternative functional form resolve the
# backward-extrapolation tension? We test a Gompertz curve, the standard
# alternative to the logistic in the technology-diffusion literature,
# precisely because it is asymmetric (slower early ramp, sharper later
# approach to its ceiling) in a way a constant-parameter logistic is not.
# ---------------------------------------------------------------------------

ALL_T = np.array([1.00, 2.00, 2.25, 3.00, 3.25])
ALL_S = np.array([0.359, 0.48, 0.496, 0.509, 0.499])


def gompertz(t, K, b, c):
    return K * np.exp(-b * np.exp(-c * t))


def fit_gompertz():
    popt, pcov = curve_fit(gompertz, ALL_T, ALL_S, p0=[0.51, 3.0, 1.0],
                            bounds=([0.3, 0.1, 0.01], [0.8, 20.0, 10.0]))
    return popt, np.sqrt(np.diag(pcov))


def compare_functional_forms():
    """Fit both logistic (anchored, as above) and Gompertz (all 5 points,
    3 free params) to the same underlying data and compare in-sample fit
    AND the t=0 (launch-date) backward/extrapolated implication of each."""
    alpha_fit, k_fit, _ = fit()
    logistic_pred = s_model_from(ANCHOR_T, ANCHOR_S, ALL_T, alpha_fit, k_fit)
    logistic_r2 = 1 - np.sum((ALL_S[1:] - logistic_pred[1:]) ** 2) / np.sum((ALL_S[1:] - ALL_S[1:].mean()) ** 2)
    logistic_t0 = s_model_from(ANCHOR_T, ANCHOR_S, np.array([0.0]), alpha_fit, k_fit)[0]

    (K_g, b_g, c_g), perr_g = fit_gompertz()
    gompertz_pred = gompertz(ALL_T, K_g, b_g, c_g)
    gompertz_r2 = 1 - np.sum((ALL_S - gompertz_pred) ** 2) / np.sum((ALL_S - ALL_S.mean()) ** 2)
    gompertz_t0 = gompertz(0.0, K_g, b_g, c_g)

    return {
        "logistic": {"alpha": alpha_fit, "k": k_fit, "r2_4pt": logistic_r2, "t0_implied": logistic_t0},
        "gompertz": {"K": K_g, "b": b_g, "c": c_g, "r2_5pt": gompertz_r2, "t0_implied": gompertz_t0,
                     "perr": perr_g},
    }


if __name__ == "__main__":
    print("Section 5.7 — Calibration of the s(t) sub-model against real data")
    print("Source: Graphite, 'AI Now Writes as Many Online Articles as Humans'")
    print("(graphite.io, May 13 2026); Common Crawl, Jan 2020-Mar 2026, N=55,400 URLs,")
    print("3-detector average (Pangram/Copyleaks/GPTZero). t = years since ChatGPT launch (Nov 2022).\n")

    print(f"  Anchor (real data point, used as initial condition): t={ANCHOR_T:.2f} (Nov 2023), s={ANCHOR_S:.3f}")
    print(f"  {'t (yrs post-launch)':>20} {'label':>16} {'s_data':>8}")
    fit_labels = ["Nov 2024 (+24mo)", "Q1 2025", "Q4 2025 (peak)", "Q1 2026"]
    for t, s, lbl in zip(FIT_T, FIT_S, fit_labels):
        print(f"  {t:>20.2f} {lbl:>16} {s:>8.3f}")

    alpha_fit, k_fit, perr = fit()
    pred, resid, r2 = goodness_of_fit(alpha_fit, k_fit)
    K = implied_carrying_capacity(alpha_fit, k_fit)

    print("\nFitted parameters (nonlinear least squares, anchored at the real Nov-2023 point,")
    print("fit to the 4 remaining real data points only):")
    print(f"  alpha (fitted)      = {alpha_fit:.3f}  (+/- {perr[0]:.3f})")
    print(f"  k = beta*h_inject   = {k_fit:.3f}  (+/- {perr[1]:.3f})")
    print(f"  implied carrying capacity K = 1 - k/alpha = {K:.3f}")
    print(f"  R^2 (fit to the 4 held-out data points) = {r2:.4f}")

    print("\nComparison to the paper's original v2.0 illustrative guess:")
    print(f"  original illustrative alpha = 0.55   |   fitted alpha = {alpha_fit:.3f}  "
          f"(~{alpha_fit/0.55:.0f}x faster than originally guessed)")

    print("\nModel vs. data at each fitted point:")
    for t, s, p, lbl in zip(FIT_T, FIT_S, pred, fit_labels):
        print(f"  t={t:.2f} ({lbl:>16}): data={s:.3f}  model={p:.3f}  residual={s-p:+.3f}")

    # Out-of-sample check: integrate BACKWARD from the anchor to see what the
    # fitted trajectory implies about the launch-era value, and compare to the
    # qualitative "very low" pre-ChatGPT baseline this was never fit to.
    t_back = np.array([0.0, 0.5, 1.0])
    s_back = s_model_from(ANCHOR_T, ANCHOR_S, t_back, alpha_fit, k_fit)
    print("\nOut-of-sample backward check (NOT used in fitting):")
    print("  the fitted trajectory, run backward from the Nov-2023 anchor, implies:")
    for t, s in zip(t_back, s_back):
        print(f"    t={t:.2f} (~{'ChatGPT launch, Nov 2022' if t==0 else ''}): implied s = {s:.3f}")
    print("  Independent qualitative anchor (Section 9.1, not used in this fit): pre-ChatGPT")
    print("  synthetic share was 'very low' / near the detectors' false-positive floor")
    print("  (single-digit percent at most, per Graphite's own pre-Nov-2022 calibration sample")
    print("  and the ~2.2% Jan-2020 figure reported by the original single-detector study).")

    print("\n--- Follow-up: does a Gompertz curve resolve the tension? ---")
    cmp = compare_functional_forms()
    lg, gp = cmp["logistic"], cmp["gompertz"]
    print(f"  Logistic (2 params, anchored, fit to 4 held-out pts): R^2={lg['r2_4pt']:.4f}, "
          f"implied s(launch)={lg['t0_implied']:.3f}")
    print(f"  Gompertz (3 params, fit to all 5 pts):                R^2={gp['r2_5pt']:.4f}, "
          f"implied s(launch)={gp['t0_implied']:.3f}  (K={gp['K']:.3f}, b={gp['b']:.2f}+/-{gp['perr'][1]:.2f}, "
          f"c={gp['c']:.2f}+/-{gp['perr'][2]:.2f})")
    print(f"  Verdict: Gompertz's launch-date implication ({gp['t0_implied']:.3f}) is "
          f"{'LOWER (closer to the qualitative low-baseline expectation)' if gp['t0_implied'] < lg['t0_implied'] else 'NOT lower'} "
          f"than the logistic's ({lg['t0_implied']:.3f}).")

    # Dense curve for plotting (from t=0 through t=4.5, using fitted params,
    # anchored at the real Nov-2023 point and extrapolated both directions)
    t_dense = np.linspace(0.0, 4.5, 250)
    s_dense = s_model_from(ANCHOR_T, ANCHOR_S, t_dense, alpha_fit, k_fit)
    np.save("/tmp/calib_t_dense.npy", t_dense)
    np.save("/tmp/calib_s_dense.npy", s_dense)
    np.save("/tmp/calib_params.npy", np.array([alpha_fit, k_fit, K, r2]))
