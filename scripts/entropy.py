"""
entropy.py — Entropy Taxonomy and Decay Measures (Section 10).

Implements:
  - Shannon entropy (Section 2.1), the common primitive underlying H_stat,
    H_sem, H_ep, and H_auth (Section 10.1) once each is reduced to a
    distribution over (tokens / claims / justifications / authors).
  - novelty_decay_rate (Section 10.3)
  - citation_entropy (Section 10.4) — a direct application of Shannon
    entropy to a distribution over primary sources.

H_sem's epistemic half-life is computed from the dynamic model directly
(see dynamics.epistemic_half_life); it is not re-derived here.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Mapping, Sequence


def shannon_entropy(distribution: Mapping[str, float], base: float = 2.0) -> float:
    """
    H(X) = - sum_x p(x) * log_b p(x)

    `distribution` may be raw non-negative counts/weights; it is normalized
    internally. Entries with probability 0 contribute 0 (by convention,
    matching the standard 0*log(0) = 0 limit).
    """
    total = sum(distribution.values())
    if total <= 0:
        raise ValueError("distribution must have positive total mass")
    h = 0.0
    for count in distribution.values():
        if count <= 0:
            continue
        p = count / total
        h -= p * math.log(p, base)
    return h


def entropy_from_labels(labels: Iterable[str], base: float = 2.0) -> float:
    """Convenience wrapper: Shannon entropy of a raw sequence of labels."""
    counts = Counter(labels)
    return shannon_entropy(counts, base=base)


# ---------------------------------------------------------------------------
# Section 10.1 — Four entropy types, as named computations over labeled data
# ---------------------------------------------------------------------------

def h_stat(token_or_ngram_labels: Iterable[str], base: float = 2.0) -> float:
    """
    H_stat — statistical/surface entropy: Shannon entropy over a token,
    n-gram, or stylistic-feature label distribution (Section 10.1).
    What perplexity-based detectors approximate indirectly.
    """
    return entropy_from_labels(token_or_ngram_labels, base=base)


def h_sem(claim_cluster_labels: Iterable[str], base: float = 2.0) -> float:
    """
    H_sem — semantic entropy: Shannon entropy over a distribution of
    *distinct claim/idea clusters* (e.g. output of a claim-clustering or
    paraphrase-clustering pipeline), abstracting away surface wording.
    """
    return entropy_from_labels(claim_cluster_labels, base=base)


def h_ep(justification_labels: Iterable[str], base: float = 2.0) -> float:
    """
    H_ep — epistemic (justificatory) entropy: Shannon entropy over the
    distribution of distinct *grounds for belief* (e.g. "peer-reviewed
    study", "named primary source", "unsourced assertion", "anecdote").
    Low H_ep indicates uniformly weak grounding even where H_sem is high
    (Section 10.1's worked example: diverse but evidence-free health claims).
    """
    return entropy_from_labels(justification_labels, base=base)


def h_auth(true_author_cluster_labels: Iterable[str], base: float = 2.0) -> float:
    """
    H_auth — authorship entropy: Shannon entropy over *true, deduplicated*
    authorial source clusters (e.g. stylometric or behavioral clustering
    output), not raw byline counts. Section 10.1's worked example: 1,000
    distinct bylines tracing to one content-farm operation should collapse
    to H_auth ~ 0 once clustered correctly, despite apparent byline diversity.
    """
    return entropy_from_labels(true_author_cluster_labels, base=base)


def entropy_taxonomy_report(
    *,
    tokens: Iterable[str],
    claim_clusters: Iterable[str],
    justifications: Iterable[str],
    author_clusters: Iterable[str],
    base: float = 2.0,
) -> dict:
    """
    Compute all four entropy types for a corpus and return them together,
    per Section 10.1's recommendation to "report all four rather than
    collapsing them into a single number prematurely."
    """
    return {
        "H_stat": h_stat(tokens, base=base),
        "H_sem": h_sem(claim_clusters, base=base),
        "H_ep": h_ep(justifications, base=base),
        "H_auth": h_auth(author_clusters, base=base),
    }


# ---------------------------------------------------------------------------
# Section 10.3 — Novelty decay rate
# ---------------------------------------------------------------------------

def novelty_decay_rate(
    novelty_scores_by_period: Sequence[Sequence[float]],
    period_length: float = 1.0,
) -> list[float]:
    """
    delta_novelty(t) = - d/dt [ (1/n_t) * sum_{d in new(t)} NS(d) ]

    Given novelty scores for newly-indexed documents bucketed into discrete
    time periods, returns the (negative-of-)first-difference of the mean
    Novelty Score across consecutive periods, divided by `period_length` —
    a discrete-time finite-difference estimate of delta_novelty(t).

    A positive value indicates novelty is declining (the "rising
    delta_novelty is a leading indicator of heat death" case in Section 10.3).
    """
    if len(novelty_scores_by_period) < 2:
        raise ValueError("need at least two periods to compute a rate of change")

    means = [
        (sum(period) / len(period)) if period else 0.0
        for period in novelty_scores_by_period
    ]
    rates = []
    for i in range(1, len(means)):
        d_mean = means[i] - means[i - 1]
        rates.append(-d_mean / period_length)
    return rates


# ---------------------------------------------------------------------------
# Section 10.4 — Citation entropy
# ---------------------------------------------------------------------------

def citation_entropy(primary_source_citations: Iterable[str], base: float = 2.0) -> float:
    """
    H_cite — Shannon entropy over the distribution of distinct *primary
    sources* cited (directly or transitively) across a corpus of secondary
    content (Section 10.4).

    `primary_source_citations` should already be resolved to primary-source
    identifiers (e.g. following paraphrase chains back to the underlying
    wire-service report), not raw secondary-article citations.
    """
    return entropy_from_labels(primary_source_citations, base=base)


if __name__ == "__main__":
    # Worked examples mirroring Section 10.1's illustrations.

    # H_stat vs H_sem divergence: AI-paraphrased versions of one wire report.
    # High lexical variety (high H_stat) but all tracing to one claim cluster
    # (low H_sem).
    paraphrase_tokens = [f"variant_{i}" for i in range(50)]  # 50 distinct surface forms
    paraphrase_claim_clusters = ["wire_report_X"] * 50       # all the same underlying claim

    print("Paraphrase-farm example:")
    print(f"  H_stat (surface variety)   = {h_stat(paraphrase_tokens):.3f} bits")
    print(f"  H_sem  (claim diversity)   = {h_sem(paraphrase_claim_clusters):.3f} bits "
          "(near zero: one claim, many wordings)")

    # H_sem high, H_ep near zero: diverse but unevidenced health claims.
    health_claim_clusters = [f"claim_{i}" for i in range(20)]
    health_justifications = ["unsourced_assertion"] * 20

    print("\nDiverse-but-ungrounded health claims example:")
    print(f"  H_sem (claim diversity)        = {h_sem(health_claim_clusters):.3f} bits")
    print(f"  H_ep  (justification diversity)= {h_ep(health_justifications):.3f} bits "
          "(near zero: diverse claims, uniformly absent evidence)")

    # H_auth collapse despite many distinct bylines.
    apparent_bylines = [f"byline_{i}" for i in range(1000)]
    true_author_clusters = ["content_farm_operator_A"] * 1000

    print("\nByline-laundering example:")
    print(f"  apparent byline entropy        = {entropy_from_labels(apparent_bylines):.3f} bits")
    print(f"  H_auth (true author clusters)  = {h_auth(true_author_clusters):.3f} bits "
          "(near zero: one operator behind 1,000 bylines)")

    # Citation entropy: many secondary articles, few primary sources.
    citations = (["wire_service_A"] * 600 + ["wire_service_B"] * 350
                 + ["independent_investigation_C"] * 50)
    print(f"\nCitation entropy across 1,000 secondary articles: "
          f"H_cite = {citation_entropy(citations):.3f} bits")

    # Novelty decay rate.
    periods = [
        [0.8, 0.75, 0.82, 0.79],   # period 1
        [0.6, 0.65, 0.58, 0.62],   # period 2
        [0.4, 0.42, 0.39, 0.41],   # period 3
    ]
    rates = novelty_decay_rate(periods)
    print(f"\nNovelty decay rate across periods 1->2, 2->3: "
          f"{[round(r, 3) for r in rates]} (positive = novelty falling)")