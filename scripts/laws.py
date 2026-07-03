"""
laws.py — The Three Laws of Epistemic Signal Value (Section 3)
and the Epistemic Debt equation (Section 4.3).

These are comparative-static relationships, not trajectories: given a level
of synthetic saturation, they tell you which direction signal value moves,
not how fast saturation itself rises over time. For the trajectory model,
see dynamics.py.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


# ---------------------------------------------------------------------------
# Law I — The Scarcity-Value Theorem
# ---------------------------------------------------------------------------

def law1_scarcity_value(h_net: float, h_max: float, k: float = 1.0) -> float:
    """
    V(s) = k * exp(H_net / H_max)

    Market value of a cryptographically verified human-authored signal,
    as a function of current vs. maximum epistemic entropy of the network.

    Parameters
    ----------
    h_net : current epistemic entropy of the indexed web (H_net)
    h_max : theoretical maximum entropy (H_max)
    k     : baseline value constant, anchored to a reference year (default 1.0)

    Returns
    -------
    float : V(s), market value of the verified signal
    """
    if h_max <= 0:
        raise ValueError("h_max must be positive")
    return k * math.exp(h_net / h_max)


# ---------------------------------------------------------------------------
# Law II — The SNR Theorem
# ---------------------------------------------------------------------------

def law2_snr(information_content: float, synthetic_noise: float) -> float:
    """
    SNR(p) = I(p) / (I(p) + N_synth(p))

    Signal-to-noise ratio of a single page/document, bounded to [0, 1].

    Parameters
    ----------
    information_content : I(p), genuine information content (bits, relative
                           to a pre-synthetic baseline)
    synthetic_noise      : N_synth(p), synthetic/redundant content (bits)

    Returns
    -------
    float in [0, 1]
    """
    if information_content < 0 or synthetic_noise < 0:
        raise ValueError("I(p) and N_synth(p) must be non-negative")
    denom = information_content + synthetic_noise
    if denom == 0:
        # No content at all is, by convention, treated as zero signal.
        return 0.0
    return information_content / denom


# ---------------------------------------------------------------------------
# Law III — The Verification Premium
# ---------------------------------------------------------------------------

def law3_verification_premium(
    p_unverified: float, lam: float, t: float
) -> float:
    """
    P(s_verified) = P(s_unverified) * exp(lambda * t)

    Parameters
    ----------
    p_unverified : price/value of unverified content
    lam          : proliferation rate of synthetic content (lambda, >= 0)
    t            : time since saturation onset (~2022 reference anchor)

    Returns
    -------
    float : price/value of verified content
    """
    return p_unverified * math.exp(lam * t)


# ---------------------------------------------------------------------------
# Section 4.3 — The Epistemic Debt Equation
# ---------------------------------------------------------------------------

@dataclass
class Document:
    """A single document/page entering the epistemic debt computation."""
    doc_id: str
    content_volume: float    # C(d): tokens
    snr: float                # SNR(d) in [0, 1]
    attention_weight: float   # A(d): pagerank / traffic share / impression share


def epistemic_debt(corpus: Sequence[Document]) -> float:
    """
    E_D(C) = sum_d [ C(d) * (1 - SNR(d)) ] * A(d)

    Total attention directed at content that provides no epistemic value.
    Treats A(d) as exogenous (the simple product form flagged in Section 4.3
    as a conservative floor once AI-agent-driven attention manufacturing,
    Section 7.2, is taken into account — see `epistemic_debt_endogenous_A`
    for a first-pass adjustment).
    """
    total = 0.0
    for d in corpus:
        if not (0.0 <= d.snr <= 1.0):
            raise ValueError(f"SNR for {d.doc_id} must be in [0, 1]")
        total += d.content_volume * (1.0 - d.snr) * d.attention_weight
    return total


def epistemic_debt_endogenous_A(
    corpus: Sequence[Document], inflation_strength: float = 1.0
) -> float:
    """
    A first-pass, explicitly non-canonical adjustment gestured at in
    Section 4.3's closing note and listed as Appendix C, Item 12
    (endogenous attention modeling).

    Rather than treating A(d) as independent of (1 - SNR(d)), this
    inflates the attention weight of low-SNR documents by a factor
    proportional to (1 - SNR(d)), modeling the claim that low-SNR
    corpora exhibit *systematically* (not randomly) inflated attention
    via bot traffic, engagement farming, and AI-agent re-citation.

    This is a toy adjustment for illustration, not a fitted model;
    Appendix C, Item 12 explicitly leaves the full endogenous-A(d)
    model as an open research item.
    """
    total = 0.0
    for d in corpus:
        if not (0.0 <= d.snr <= 1.0):
            raise ValueError(f"SNR for {d.doc_id} must be in [0, 1]")
        inflated_A = d.attention_weight * (
            1.0 + inflation_strength * (1.0 - d.snr)
        )
        total += d.content_volume * (1.0 - d.snr) * inflated_A
    return total


if __name__ == "__main__":
    # Minimal smoke test / usage example.
    print("Law I  V(s) at H_net/H_max = 0.9:", law1_scarcity_value(0.9, 1.0, k=2.72))
    print("Law II SNR(p) for I=2, N_synth=18:", law2_snr(2.0, 18.0))
    print("Law III premium at lambda=0.3, t=4:", law3_verification_premium(1.0, 0.3, 4.0))

    corpus = [
        Document("d1", content_volume=1000, snr=0.05, attention_weight=0.8),
        Document("d2", content_volume=500, snr=0.9, attention_weight=0.1),
        Document("d3", content_volume=2000, snr=0.1, attention_weight=0.6),
    ]
    print("Epistemic debt (exogenous A):", epistemic_debt(corpus))
    print("Epistemic debt (endogenous A, toy):", epistemic_debt_endogenous_A(corpus))