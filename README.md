# Epistemic Heat Death and the Signal-to-Noise Ratio of the Global Web

**Author:** Jarosław Szulc · [psyll.com](https://psyll.com) · jarek@psyll.com

**Working paper · v2.1 · July 2026 · Draft for public comment**

A theoretical framework for the post-AI information ecology: as AI-generated text, images, audio, and video come to dominate newly published web content, the web can look more abundant than ever while its actual information content - distinct ideas, grounded claims, accountable authorship - quietly collapses. This paper calls that failure mode **epistemic heat death** and builds a formal apparatus around it: three governing laws of signal value, a coupled-ODE dynamical model, a proposed Signal-to-Noise Ratio (SNR) index, and a technical/economic blueprint (the cryptographic provenance stack) for an alternative equilibrium.

**v2.1** is a verification pass, not a new theoretical version: every quantitative claim in Section 5 has been re-run against the reference code, all ten in-text figures have been generated (they were broken links before), and the empirical anchors in Section 9/11 have been independently fact-checked - see [Appendix J](<Epistemic Heat Death and the Signal-to-Noise Ratio of the Global Web.md>) in the paper for the full record, including the one correction and one removed citation that came out of that check. It does **not** claim to have empirically confirmed the framework's own theoretical claims - see Appendix J.4.

## What's in this repo

- **[`Epistemic Heat Death and the Signal-to-Noise Ratio of the Global Web.md`](<Epistemic Heat Death and the Signal-to-Noise Ratio of the Global Web.md>)** - the full paper
- **`scripts/`** - reference Python implementations for the paper's formal models, one module per section, each runnable standalone, plus `make_figures.py` which generates every chart in `charts/`
- **`charts/`** - all ten figures referenced in the paper, generated directly from the reference implementations (or, for the four purely conceptual diagrams, clearly labeled as illustrative schematics)

### Scripts → paper sections

| Script | Paper section | Depends on |
|---|---|---|
| `laws.py` | §3–4 - the three laws of epistemic signal value, and the epistemic debt equation | stdlib |
| `dynamics.py` | §5 - the coupled-ODE dynamic model, scenario trajectories, sensitivity grid, AEO intervention scenario | `numpy`, `scipy` |
| `snr_index.py` | §6 - the three-level SNR index (document / domain / global web) and the EVI metric | stdlib |
| `entropy.py` | §10 - the entropy taxonomy (statistical, semantic, epistemic, authorship) and decay measures | stdlib |
| `make_figures.py` | generates all ten `charts/fig_*.png` files from the four modules above | `matplotlib`, + the above |

Each script runs on its own and prints worked examples tied to the paper's numbered results:

```bash
pip install numpy scipy matplotlib
python3 scripts/dynamics.py
python3 scripts/laws.py
python3 scripts/snr_index.py
python3 scripts/entropy.py
python3 scripts/make_figures.py   # regenerates charts/*.png
```

`dynamics.py`, for instance, reproduces the baseline trajectory (§5.2), the scenario comparison (§5.3), the sensitivity-grid extremes (§5.4), and the AEO intervention comparison (§5.5) as console output - and as of v2.1, the numbers printed to the console are the same numbers quoted in the paper text, checked by direct re-execution rather than transcription.

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