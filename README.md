# Epistemic Heat Death and the Signal-to-Noise Ratio of the Global Web

**Author:** Jarosław Szulc · [psyll.com](https://psyll.com) · jarek@psyll.com

**Working paper · v2.3 · July 2026 · Draft for public comment**

A theoretical framework for the post-AI information ecology: as AI-generated text, images, audio, and video come to dominate newly published web content, the web can look more abundant than ever while its actual information content - distinct ideas, grounded claims, accountable authorship - quietly collapses. This paper calls that failure mode **epistemic heat death** and builds a formal apparatus around it: three governing laws of signal value, a coupled-ODE dynamical model, a proposed Signal-to-Noise Ratio (SNR) index, and a technical/economic blueprint (the cryptographic provenance stack) for an alternative equilibrium.

**v2.3** resolves a puzzle v2.2 left open: fitting the model's synthetic-share equation to real data (Graphite/Common Crawl) implied an oddly high pre-ChatGPT baseline (§5.7.3); testing a Gompertz alternative (§5.7.5) fits far better (`R²=0.994` vs `0.806`) and resolves it. It also adds a first, fully-disclosed real-data pilot of the `H_cite`/`H_sem` measures on independent news coverage of one shared event (§10.6), and a standalone, implementable **[MVP-0 content-provenance spec](mvp0-content-provenance-spec.md)** - an HTTP header, HTML meta tag, schema.org mapping, and site-wide well-known-URI convention any publisher could adopt tomorrow.

**v2.2** added the first calibration attempt; **v2.1** was a verification pass on the pre-existing text (every quantitative claim in the then-existing Section 5 re-run against the reference code, all in-text figures generated, empirical anchors fact-checked - Appendix J). None of v2.1, v2.2, or v2.3 claims to have empirically confirmed the framework's own theoretical claims - see Appendix J.4 and Section 5.7.4.

## What's in this repo

- **[`Epistemic Heat Death and the Signal-to-Noise Ratio of the Global Web.md`](<Epistemic Heat Death and the Signal-to-Noise Ratio of the Global Web.md>)** - the full paper
- **[`MVP-0 Content Provenance Spec`](MVP-0 Content Provenance Spec.md)** - standalone, implementable MVP-0 technical spec (companion to §13.5)
- **`scripts/`** - reference Python implementations for the paper's formal models, one module per section, each runnable standalone
- **`charts/`** - all eleven figures referenced in the paper, generated directly from the reference implementations (or, for the four purely conceptual diagrams, clearly labeled as illustrative schematics)

### Scripts → paper sections

| Script | Paper section | Depends on |
|---|---|---|
| `laws.py` | §3–4 - the three laws of epistemic signal value, and the epistemic debt equation | stdlib |
| `dynamics.py` | §5.1–5.6 - the coupled-ODE dynamic model, scenario trajectories, sensitivity grid, AEO intervention scenario | `numpy`, `scipy` |
| `calibration.py` | §5.7 - fits the model's synthetic-share sub-equation against real Graphite/Common-Crawl data; §5.7.5 tests a Gompertz alternative | `numpy`, `scipy` |
| `snr_index.py` | §6 - the three-level SNR index (document / domain / global web) and the EVI metric | stdlib |
| `entropy.py` | §10.1-10.4 - the entropy taxonomy (statistical, semantic, epistemic, authorship) and decay measures | stdlib |
| `pilot_jobsreport.py` | §10.6 - real-data `H_cite`/`H_sem` pilot on independent coverage of the June 2026 US jobs report | `entropy.py` |
| `make_figures.py` | generates all eleven `charts/fig_*.png` files from the modules above | `matplotlib`, + the above |

Each script runs on its own and prints worked examples tied to the paper's numbered results:

```bash
pip install numpy scipy matplotlib
python3 scripts/dynamics.py
python3 scripts/calibration.py       # §5.7 — the real-data fit, and §5.7.5's Gompertz comparison
python3 scripts/laws.py
python3 scripts/snr_index.py
python3 scripts/entropy.py
python3 scripts/pilot_jobsreport.py  # §10.6 — the H_cite / H_sem real-data pilot
python3 scripts/make_figures.py      # regenerates charts/*.png
```

`dynamics.py`, for instance, reproduces the baseline trajectory (§5.2), the scenario comparison (§5.3), the sensitivity-grid extremes (§5.4), and the AEO intervention comparison (§5.5) as console output - and as of v2.1, the numbers printed to the console are the same numbers quoted in the paper text, checked by direct re-execution rather than transcription. `calibration.py` fits `α` and `k=β·h_inject` against real data and prints both the in-sample fit quality and the out-of-sample backward-extrapolation check, plus (new in v2.3) the Gompertz comparison that resolves it. `pilot_jobsreport.py` prints the full citation tally and semantic-clustering classification behind §10.6's numbers, specifically so a skeptical reader can audit and dispute the classification rather than take it on trust.

## Key claims

- The web is undergoing a measurable rise in epistemic entropy that, absent intervention, tends toward a degenerate equilibrium - epistemic heat death.
- Diversity loss isn't one phenomenon but at least four loosely-coupled ones (statistical, semantic, epistemic, authorship entropy), which can move independently and even in opposite directions.
- Pageviews and engagement metrics are structurally broken as value proxies once a substantial share of traffic and content production is non-human.
- The same mechanisms extend to images, audio, and video (synthetic reality collapse), with failure modes - chiefly provenance-metadata stripping on re-compression - that text alone doesn't have.
- Epistemic heat death is not distributionally neutral: it produces winners and losers along lines of expertise, language, geography, and institutional access, and is exploitable as a tool of state and corporate power.
- In simulation, the model's `SNR_proxy(t)` declines monotonically across the full tested parameter grid; the epistemic half-life is more sensitive to the model-collapse rate than to the raw synthetic-growth rate, implying collapse-targeted interventions have more leverage than volume-targeted ones. These are flagged explicitly as structural properties of an illustrative, uncalibrated toy model, not forecasts.

The paper is also explicit about what it doesn't yet know - see §9.5 (falsification conditions), §5.6 (model limitations), §15 (objections and responses, including a self-directed unfalsifiability objection), and, new in v2.1, Appendix J (an independent verification and fact-check record, including what could and could not be confirmed).

## Status

Working paper, draft for public comment. Comments and empirical challenges are welcomed - see the contact details above.

## License

This entire repository - paper text, figures, and code - is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reproduction, citation, critique, and extension are permitted with attribution. See [`LICENSE`](LICENSE) for the full terms.
