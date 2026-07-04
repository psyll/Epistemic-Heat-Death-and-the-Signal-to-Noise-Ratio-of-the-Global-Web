"""
pilot_jobsreport.py — Section 10.6: a first real-data pilot for H_cite and H_sem.

Case study: coverage of the BLS "Employment Situation - June 2026" report,
released Thu July 2, 2026, 8:30am ET (bls.gov). Seven independent secondary
sources covering the same release were read directly (via web search/fetch)
on July 3, 2026: CNBC, Fox Business, Center for American Progress (CAP),
Indeed Hiring Lab, U.S. Dept. of Labor (Acting Secretary Sonderling
statement), ABC News, CNN Business.

METHODOLOGY AND ITS LIMITS (read this before the numbers below):
This is a pilot of the *method*, not a validated measurement instrument.
The citation tabulation (WHICH primary sources each article names) is a
comparatively low-judgment task -- close to a factual tally. The semantic
clustering (WHICH articles share a "claim cluster") is a much higher-
judgment task, done here by one reader (Claude) applying its own reading
comprehension, not a blinded, multi-rater, inter-rater-reliability-tested
protocol. We report our classification transparently below specifically so
a skeptical reader can audit and disagree with it -- that transparency is
the actual check on this pilot's central subjective step, not a footnote.
Because H_sem is sensitive to clustering granularity (a point the paper's
Section 10.5 already makes in the abstract), we report it at two different
granularities rather than picking one and presenting it as definitive.
"""

from __future__ import annotations

import sys
sys.path.insert(0, ".")
from entropy import citation_entropy, h_sem, entropy_from_labels

# ---------------------------------------------------------------------------
# Citation tabulation: one entry per (article, primary source cited) pair.
# "BLS" = the Employment Situation release itself. Everything else is a
# distinct named primary source (an official statement, a named economist's
# note/quote, a named third-party data tool, or "own_data" for an outlet's
# proprietary analysis not attributed to a third party).
# ---------------------------------------------------------------------------

CITATIONS = (
    # CNBC
    ["BLS", "fed_chair_warsh_remarks", "jefferies_note"]
    # Fox Business
    + ["BLS", "lseg_poll"]
    # Center for American Progress
    + ["BLS", "cleveland_fed_nowcast"]
    # Indeed Hiring Lab
    + ["BLS", "own_data_indeed"]
    # U.S. Department of Labor (Sonderling statement)
    + ["BLS"]
    # ABC News
    + ["BLS", "cme_fedwatch_tool", "fed_chair_warsh_remarks"]
    # CNN Business
    + ["BLS", "pantheon_macro_note", "nerdwallet_interview", "pnc_economist_quote", "indeed_hiring_lab_as_source"]
)

ARTICLE_SOURCE_COUNTS = {
    "CNBC": 3, "Fox Business": 2, "CAP": 2, "Indeed Hiring Lab": 2,
    "DOL (Sonderling)": 1, "ABC News": 3, "CNN Business": 5,
}

# ---------------------------------------------------------------------------
# Semantic (claim) clustering of the 7 SECONDARY articles (BLS excluded --
# it is the primary source being reported on, not a secondary claim about
# it). Two granularities, both defensible, given deliberately to make
# Section 10.5's "no unique clustering method" point concrete rather than
# asserted.
# ---------------------------------------------------------------------------

# COARSE: articles sharing a substantially overlapping analytical throughline
# are merged into one cluster.
COARSE_CLUSTERS = (
    ["mainstream_cooling_growth"] * 4       # CNBC, Fox Business, ABC, CNN
    + ["progressive_distributional_critique"] * 1   # CAP
    + ["original_structural_framework"] * 1          # Indeed ("slack water")
    + ["administration_political_framing"] * 1       # DOL/Sonderling
)

# FINE: each article treated as its own distinct claim cluster (i.e., we
# judge all seven as sufficiently distinct in emphasis/framing/sourcing to
# not collapse any two together).
FINE_CLUSTERS = [f"article_{i}" for i in range(7)]  # 7 singleton clusters by construction

ARTICLE_LABELS = ["CNBC", "Fox Business", "CAP", "Indeed Hiring Lab",
                  "DOL (Sonderling)", "ABC News", "CNN Business"]
COARSE_ASSIGNMENT = ["mainstream_cooling_growth", "mainstream_cooling_growth",
                      "progressive_distributional_critique", "original_structural_framework",
                      "administration_political_framing", "mainstream_cooling_growth",
                      "mainstream_cooling_growth"]


if __name__ == "__main__":
    print("Section 10.6 pilot — BLS June 2026 jobs report coverage (7 secondary articles, 1 primary source)\n")

    print("Citation tally (article -> # distinct primary sources named):")
    for art, n in ARTICLE_SOURCE_COUNTS.items():
        print(f"  {art:20s} {n}")
    print(f"  Total citation instances: {len(CITATIONS)}")

    hc = citation_entropy(CITATIONS)
    print(f"\nH_cite (Shannon entropy over {len(set(CITATIONS))} distinct primary sources, "
          f"{len(CITATIONS)} instances) = {hc:.3f} bits")
    print("  Reference points: H_cite=0 would mean every citation instance points to the same")
    print("  single source (the paper's 'three wire reports' toy example); the maximum possible")
    print(f"  entropy for {len(set(CITATIONS))} equally-weighted distinct sources would be "
          f"{__import__('math').log2(len(set(CITATIONS))):.3f} bits.")

    print("\nSemantic clustering (our read, given for audit):")
    for art, cl in zip(ARTICLE_LABELS, COARSE_ASSIGNMENT):
        print(f"  {art:20s} -> {cl}")

    h_coarse = h_sem(COARSE_CLUSTERS)
    h_fine = h_sem(FINE_CLUSTERS)
    print(f"\nH_sem (coarse, 4 clusters over 7 articles) = {h_coarse:.3f} bits")
    print(f"H_sem (fine, 7 singleton clusters)          = {h_fine:.3f} bits  (= log2(7), by construction)")
    print("  The 1.14-bit gap between these two numbers, from the SAME 7 articles, IS Section 10.5's")
    print("  'no unique clustering method' caveat made concrete rather than asserted.")

    print("\nHeadline lexical variety (crude H_stat proxy — each headline is trivially distinct):")
    headlines = [f"headline_{i}" for i in range(7)]
    print(f"  entropy over 7 distinct headlines = {entropy_from_labels(headlines):.3f} bits "
          f"(= log2(7), maximal by construction — headlines are ALWAYS lexically distinct; "
          "this is exactly why H_stat is a weak signal on its own, Section 10.1)")

    print("\nReading (see paper Section 10.6 for the full discussion):")
    print("  Despite 7/7 secondary articles sharing ONE dominant primary source (BLS) -- the")
    print("  scenario the paper's original worked example associates with LOW H_cite and LOW")
    print("  H_sem together (AI paraphrase farms) -- this real, human-journalism corpus shows")
    print(f"  moderate-to-high H_cite ({hc:.2f} bits, driven by each outlet's independent expert")
    print(f"  sourcing) AND moderate-to-high H_sem ({h_coarse:.2f}-{h_fine:.2f} bits, driven by genuinely")
    print("  distinct analytical framing). H_cite and H_sem move TOGETHER in the direction the")
    print("  paper's SNR framework treats as healthy here -- because this is skilled human")
    print("  journalism, not synthetic churnalism. That is the pilot's one substantive finding:")
    print("  the taxonomy's predicted LOW/LOW vs HIGH/HIGH coupling is visible in real data at")
    print("  least in this one case, though N=1 case study proves nothing at population scale.")
