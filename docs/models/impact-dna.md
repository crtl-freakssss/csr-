# AllocateAI — Impact DNA Fingerprint Model

**Model Version:** `dna-v1`  
**Owner:** Member B (AI / Data Pipeline)  
**Consumer:** Member C (Decision Engine) & Member D (API / Platform)  
**Contract Reference:** Technical Contract v1.0 Section 10 & 89

---

## 1. Dimensional Overview

Impact DNA is a multi-dimensional project fingerprint consisting of 6 normalized scores bounded strictly between $0.0$ and $1.0$:

| Dimension | Range | Description |
|---|---|---|
| `need_score` | $[0.0, 1.0]$ | Geographic and demographic urgency, aspirational district status. |
| `expected_impact_score` | $[0.0, 1.0]$ | Depth, sustainability, and transformative potential of intervention. |
| `cost_efficiency_score` | $[0.0, 1.0]$ | Cost per beneficiary relative to sectoral benchmarks. |
| `evidence_strength_score` | $[0.0, 1.0]$ | Rigor of baseline surveys, citations, and 3rd-party audits. |
| `scalability_score` | $[0.0, 1.0]$ | Modularity and ease of regional replication. |
| `implementation_risk_score` | $[0.0, 1.0]$ | Operational, environmental, and governance risk factors. |

---

## 2. Calculated Efficiency

$$\text{estimated\_impact\_per\_lakh} = \frac{\text{target\_count}}{\text{requested\_amount\_paise} / 10\,000\,000}$$

Where $10\,000\,000 \text{ paise} = ₹1,00,000$ (1 Lakh INR).

---

## 3. Boundary Invariant

These 6 dimensions are **AI-derived inputs**, not final allocation decisions. Member C's deterministic optimizer incorporates these scores alongside CSR saturation and marginal impact curves.
