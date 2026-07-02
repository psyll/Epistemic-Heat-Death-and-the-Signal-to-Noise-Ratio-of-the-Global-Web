"""
snr_index.py — The SNR Index: Methodology and Measurement (Section 6).

Implements the three-level measurement architecture:
  Level 1 — Document-level SNR  (SNR_doc)
  Level 2 — Domain-level SNR    (SNR_domain)
  Level 3 — Global web SNR      (SNR_web)

and the proposed pageview replacement metric, Epistemic Value per
Impression (Section 6.4, EVI).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


# ---------------------------------------------------------------------------
# Level 1 — Document-level SNR
# ---------------------------------------------------------------------------

@dataclass
class DocSignals:
    """
    The three raw signals feeding SNR_doc (Section 6.2):
      scp : Synthetic Content Probability, P(synthetic) in [0, 1]
      ns  : Novelty Score (semantic distance from reference corpus), in [0, 1]
      pv  : Provenance Verification, binary {0, 1}
    """
    doc_id: str
    scp: float
    ns: float
    pv: int


DEFAULT_WEIGHTS = {"w_scp": 0.3, "w_ns": 0.4, "w_pv": 0.3}


def snr_doc(signals: DocSignals, weights: dict = None) -> float:
    """
    SNR_doc = w_scp * (1 - SCP) + w_ns * NS + w_pv * PV

    Note: these document-level weights (w_scp, w_ns, w_pv) are deliberately
    named differently from the alpha/beta parameters of the Section 5
    dynamic model (dynamics.ModelParams), which govern corpus-level
    dynamics rather than per-document scoring. Reusing alpha/beta/gamma
    here would overload notation already defined in Section 5.
    """
    w = weights or DEFAULT_WEIGHTS
    total_w = w["w_scp"] + w["w_ns"] + w["w_pv"]
    if abs(total_w - 1.0) > 1e-6:
        raise ValueError(f"w_scp + w_ns + w_pv must equal 1 (got {total_w})")
    if signals.pv not in (0, 1):
        raise ValueError("pv must be 0 or 1")
    if not (0.0 <= signals.scp <= 1.0) or not (0.0 <= signals.ns <= 1.0):
        raise ValueError("scp and ns must be in [0, 1]")

    return (
        w["w_scp"] * (1 - signals.scp)
        + w["w_ns"] * signals.ns
        + w["w_pv"] * signals.pv
    )



# ---------------------------------------------------------------------------
# Level 2 — Domain-level SNR
# ---------------------------------------------------------------------------

@dataclass
class ScoredDoc:
    doc_id: str
    snr: float
    traffic_weight: float


def snr_domain(docs: Sequence[ScoredDoc]) -> float:
    """
    SNR_domain(D) = (1/n) * sum_i SNR_doc(d_i) * w(d_i)
    """
    if not docs:
        raise ValueError("docs must be non-empty")
    for d in docs:
        if not (0.0 <= d.snr <= 1.0):
            raise ValueError(f"SNR for {d.doc_id} must be in [0, 1] (got {d.snr})")
        if d.traffic_weight < 0:
            raise ValueError(f"traffic_weight for {d.doc_id} must be non-negative")
    n = len(docs)
    return sum(d.snr * d.traffic_weight for d in docs) / n


# ---------------------------------------------------------------------------
# Level 3 — Global web SNR
# ---------------------------------------------------------------------------

@dataclass
class DomainScore:
    domain: str
    market_share: float
    snr_domain: float


def snr_web(domains: Sequence[DomainScore], baseline: float = 1.0) -> float:
    """
    SNR_web(t) = sum_D [ market_share(D, t) * SNR_domain(D, t) ]

    Returned as a ratio to `baseline` (Section 6.2 defines
    SNR_web(2020) = 1.0 by convention).
    """
    if baseline <= 0:
        raise ValueError("baseline must be positive")
    for d in domains:
        if not (0.0 <= d.market_share <= 1.0):
            raise ValueError(f"market_share for {d.domain} must be in [0, 1] (got {d.market_share})")
        if not (0.0 <= d.snr_domain <= 1.0):
            raise ValueError(f"snr_domain for {d.domain} must be in [0, 1] (got {d.snr_domain})")
    raw = sum(d.market_share * d.snr_domain for d in domains)
    return raw / baseline


# ---------------------------------------------------------------------------
# Section 6.4 — Epistemic Value per Impression (EVI)
# ---------------------------------------------------------------------------

def evi(snr_doc_score: float, human_reader_rate: float, depth_signal: float) -> float:
    """
    EVI(p) = SNR_doc(p) * HR(p) * D(p)
    """
    for name, val in [("snr_doc_score", snr_doc_score),
                       ("human_reader_rate", human_reader_rate)]:
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"{name} must be in [0, 1]")
    if depth_signal < 0:
        raise ValueError("depth_signal must be non-negative")
    return snr_doc_score * human_reader_rate * depth_signal


if __name__ == "__main__":
    d1 = DocSignals("page-A", scp=0.1, ns=0.7, pv=1)
    d2 = DocSignals("page-B (synthetic, unverified)", scp=0.95, ns=0.05, pv=0)

    s1 = snr_doc(d1)
    s2 = snr_doc(d2)
    print(f"SNR_doc(page-A) = {s1:.3f}")
    print(f"SNR_doc(page-B) = {s2:.3f}")

    domain_score = snr_domain([
        ScoredDoc("page-A", s1, traffic_weight=0.8),
        ScoredDoc("page-B", s2, traffic_weight=0.2),
    ])
    print(f"SNR_domain        = {domain_score:.3f}")

    web_score = snr_web([
        DomainScore("news.example", market_share=0.6, snr_domain=domain_score),
        DomainScore("content-farm.example", market_share=0.4, snr_domain=0.05),
    ])
    print(f"SNR_web (ratio to baseline=1.0) = {web_score:.3f}")

    evi_a = evi(s1, human_reader_rate=0.9, depth_signal=0.6)
    evi_b = evi(s2, human_reader_rate=0.95, depth_signal=0.1)
    print(f"EVI(page-A) = {evi_a:.3f}")
    print(f"EVI(page-B) = {evi_b:.3f}  (illustrates: traffic alone does not buy EVI)")
