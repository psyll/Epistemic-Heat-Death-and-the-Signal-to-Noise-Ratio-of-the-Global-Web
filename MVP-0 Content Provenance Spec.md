# MVP-0 Content Provenance Disclosure — Technical Specification v0.1

**Status:** Draft, companion to Section 13.5 of "Epistemic Heat Death and the Signal-to-Noise Ratio of the Global Web" (Szulc, v2.3, July 2026)
**Scope:** MVP-0 only — no cryptography, no key infrastructure, no attestation network. This is the "publisher-level self-disclosure" tier described in Section 13.5: a schema, not an infrastructure.
**Non-goals:** This spec does not verify anything. It gives dishonest publishers a way to lie more precisely, exactly as robots.txt gives crawlers no enforcement mechanism against bad actors. Its value is identical in kind to robots.txt's: it costs almost nothing to adopt, it is immediately useful for the (large) majority of publishers who have no reason to lie, and it gives the ecosystem (Section 6.2's Signal A detectors, Section 13's later layers) a cheap prior to weight against other signals rather than a ground truth to trust blindly.

---

## 1. Purpose

Give any publisher, on any platform, a way to declare - per page, per section, or site-wide - whether content was human-authored, AI-assisted, or AI-generated, using existing web infrastructure (HTTP headers, HTML meta tags, or a well-known URI) rather than new cryptographic tooling. This is deliberately the *cheapest possible* first rung of the five-layer stack in Section 13.1, chosen so that adoption cost is never the reason a publisher declines to participate.

## 2. Design principles

1. **Zero new infrastructure.** No keys, no registries, no signing. If a publisher can edit an HTTP header or an HTML `<head>`, they can implement this today.
2. **Layered, not exclusive.** A publisher can adopt this at the HTTP-header level, the per-page HTML level, the structured-data level, or the site-wide level, in any combination. Layers are additive; the most specific applicable layer wins (see §6).
3. **Honesty is reputational, not cryptographic**, by design (Section 13.5). This spec makes no claim to be forgery-resistant. Layer 2 (C2PA/CSP, Section 13.1) is what adds cryptographic teeth; this spec exists so the ecosystem has *something* before that is built out for text.
4. **Machine-first, human-readable second.** Values are a small closed enum, not free text, so they can be parsed without NLP.
5. **Forward-compatible with MVP-1/2.** The same field names are designed to be trivially extendable with a signature block once Layer 1/2 (AKR/CSP) infrastructure exists (§7).

## 3. The disclosure taxonomy

Four values, matching the terms already used informally in Section 13.5:

| Value | Definition |
|---|---|
| `human-authored` | No generative-AI system was used to produce the substantive content (grammar/spell-check tooling does not disqualify this label). |
| `ai-assisted` | A human is the substantive author; generative AI was used for drafting assistance, editing, research synthesis, or similar, but a human directed the content and takes editorial responsibility for it. |
| `ai-generated` | A generative AI system produced the substantive content with no more than light human editing (fact-checking, formatting, or minor correction). |
| `undisclosed` | The publisher declines to disclose. This is a distinct, explicit value - it is not the same as omitting the field entirely (§6 on how consumers should treat each case differently). |

Absence of any tag at all is **not** equivalent to `undisclosed`; it means the publisher has not adopted this spec, and consumers should fall back entirely to Signal A-style detection (Section 6.2) with no disclosure prior.

## 4. Implementation surfaces

### 4.1 HTTP response header (page-level, preferred for dynamic sites)

```
X-Content-Origin: ai-assisted
```

Optional parameters, semicolon-separated, matching the grammar of existing structured HTTP headers (e.g. RFC 8941-style):

```
X-Content-Origin: ai-assisted; tool="claude-sonnet-5"; human-edit-pct="high"; disclosed-by="example.com"
```

- `tool` (optional, free text): name of the primary generative tool used, if disclosed.
- `human-edit-pct` (optional, enum: `none`|`low`|`medium`|`high`): coarse, self-assessed editorial involvement. Deliberately coarse rather than a fake-precise percentage, to avoid inviting spurious precision.
- `disclosed-by` (optional): the declaring domain, useful when content is syndicated and the disclosure should travel with it.

### 4.2 HTML meta tag (page-level, preferred for static sites / where header control is unavailable)

```html
<meta name="content-origin" content="ai-assisted">
<meta name="content-origin:tool" content="claude-sonnet-5">
<meta name="content-origin:human-edit-pct" content="high">
```

### 4.3 JSON-LD / schema.org structured data (page-level, for rich-result and knowledge-graph consumption)

Pending a formal schema.org extension (which this spec explicitly recommends as a Recommendation-1.1-adjacent standards-body action, Section 14.1), publishers can use schema.org's existing `additionalProperty` mechanism today without waiting for a new vocabulary term:

```json
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "Example headline",
  "additionalProperty": {
    "@type": "PropertyValue",
    "name": "contentOrigin",
    "value": "ai-assisted",
    "additionalType": "https://example.org/mvp0-content-provenance-spec#taxonomy"
  }
}
```

### 4.4 Site-wide default (well-known URI, for blanket declarations without per-page tagging)

For publishers who want a single site-wide default (e.g., a personal blog that is always human-authored, or a content operation that discloses its general practice), a `/.well-known/content-provenance` text file, modeled directly on the existing `/.well-known/security.txt` and `/robots.txt` conventions:

```
# /.well-known/content-provenance
Default: human-authored
Contact: mailto:editor@example.com
Policy: https://example.com/ai-use-policy
```

A page-level tag (§4.1-4.3) always overrides the site-wide default for that page.

## 5. Precedence rules

When multiple layers are present for the same page, apply in this order (most specific wins):

1. Per-page JSON-LD `additionalProperty` (§4.3)
2. Per-page HTTP header (§4.1)
3. Per-page HTML meta tag (§4.2)
4. Site-wide `/.well-known/content-provenance` default (§4.4)
5. No signal present → treat as fully undisclosed, no prior.

## 6. Guidance for machine consumers (crawlers, detectors, aggregators)

This spec's value is entirely in how conservatively it is *consumed*, not in how it is produced:

- Treat a self-declared `human-authored` or `ai-assisted` tag as a **weak prior**, not a verified fact - combine it with, never substitute it for, Signal A-style statistical detection (Section 6.2). A publisher's tag and a detector's independent estimate disagreeing is itself a useful, loggable signal (candidate input to Layer 3 attestation-network reputation once that layer exists, Section 13.1).
- Treat `undisclosed` as informative in itself (a publisher capable of adopting this spec who chose the explicit opt-out) - differently from no-tag-at-all (a publisher who has not engaged with the spec at all).
- Do **not** use adoption of this spec, by itself, as a positive ranking or trust signal strong enough to move search position materially (Recommendation 2.1/2.2, Section 14.2) until Layer 2+ cryptographic backing exists - doing so before then would create exactly the incentive to mislabel that Objection 3 (Section 15) already flags as a risk for the full stack, at a stage of the stack with no accountability mechanism at all.

## 7. Migration path to MVP-1

When a publisher adopts Layer 1+2 (AKR/CSP, Section 13.1), the same `X-Content-Origin` header gains a `signature` parameter pointing to the C2PA manifest or equivalent:

```
X-Content-Origin: human-authored; disclosed-by="example.com"; signature="c2pa://manifest-hash..."
```

No value in the existing taxonomy (§3) needs to change; MVP-1 only adds verifiability to a claim this spec already structures.

## 8. Worked example

A news article, substantially written by a reporter with AI-assisted research synthesis, published on a site that also maintains a site-wide default:

```
/.well-known/content-provenance:
  Default: human-authored

HTTP response for /2026/07/03/article-slug:
  X-Content-Origin: ai-assisted; tool="claude-sonnet-5"; human-edit-pct="high"; disclosed-by="example.com"
```

The page-level header overrides the site-wide default (§5, rule 1 does not apply since no JSON-LD is present here, so rule 2 - the header - wins over rule 4, the site default). A crawler implementing §6 records `ai-assisted, high human involvement, self-disclosed, unverified` as one input feature alongside its own independent Signal A estimate - not as a final answer.

---

*This specification is released under the same CC BY 4.0 license as the parent paper. It is offered as a concrete, adoptable artifact rather than only a paragraph of description, specifically because Section 13.5 argues that shipping MVP-0 immediately - even before cryptographic infrastructure exists - has a stronger case than a pure cost-benefit analysis of MVP-0 in isolation would suggest. Comments, critiques, and implementations are welcomed at the contact address in the parent paper.*
