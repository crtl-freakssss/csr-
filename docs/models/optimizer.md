# Deterministic Budget Optimizer & Base Impact Scoring Specification

## 1. Purpose
The Deterministic Budget Optimizer calculates the optimal distribution of a finite CSR budget across candidate interventions. It replaces discretionary manual allocations and probabilistic AI guesses with a verifiable mathematical optimization process. Given candidate projects, priority policy weights, and statutory/operational constraints, the optimizer computes a reproducible allocation schedule accompanied by deterministic reasoning codes.

In Phase 5, the `AllocationOptimizer` (`optimizer-v1`) integrates:
* **Phase 2 (Scoring Engine)**: `base_score` and component contributions.
* **Phase 3 (CSR Saturation Engine)**: `saturation_index` and regional context.
* **Phase 4 (Marginal Impact Engine)**: `marginal_impact_score` and incremental return.
* **Constraint Engine**: Project caps, regional caps, minimum allocation floors, and regional equity rules.

## 2. Inputs
The optimizer consumes validated payloads defined in Technical Contract v1.0:
* **Candidate Projects**: List of `Project` entities with financial requirements and demographic targets.
* **Impact DNA Fingerprints**: Extraction profiles containing `need_score`, `expected_impact_score`, `cost_efficiency_score`, `evidence_strength_score`, `scalability_score`, and `implementation_risk_score`.
* **Saturation Assessments**: Regional `SaturationResult` records reflecting local funding saturation.
* **Marginal Impact Assessments**: Incremental `MarginalImpactResult` records.
* **Optimization Request**:
  * `budget_paise`: Total available allocation budget in integer paise ($> 0$).
  * `weights`: Policy trade-off parameters (`OptimizationWeights`) summing to 1.0 (`need`, `marginal_impact`, `cost_efficiency`, `evidence`, `scalability`, `equity`, `risk_penalty`).
  * `constraints`: Operational boundaries (`OptimizationConstraints`) including project caps, regional equity requirements, and full allocation directives.
  * `marginal_increment_paise`: Incremental step size for discrete marginal optimization (default: `10,000,000` paise).

## 3. Outputs
The optimizer emits an authoritative `OptimizationResult` conforming to Technical Contract v1.0:
* **`run_id`**: Canonical identifier formatted as `OPT-XXXX`.
* **`status`**: Execution outcome status (`OptimizationStatus.COMPLETED` or `OptimizationStatus.FAILED`).
* **`budget_paise`**, **`allocated_paise`**, **`unallocated_paise`**: Financial accounting balance satisfying the invariant:
  $$\text{allocated\_paise} + \text{unallocated\_paise} = \text{budget\_paise}$$
* **`allocations`**: Ranked list of individual project `Allocation` recommendations:
  * `project_id`: Unique project reference.
  * `allocated_amount_paise`: Recommended capital in integer paise.
  * `base_score`, `marginal_impact_score`, `saturation_index`.
  * `reason_codes`: Deterministic rationale tags (e.g., `HIGH_MARGINAL_IMPACT`, `LOW_SATURATION`, `REGIONAL_CAP`).
  * `rank`: Integer priority ordering ($1, 2, \dots$).
  * `allocation_context`: Explainability dictionary (`requested_amount_paise`, `remaining_need_paise`, `allocation_fraction`, `optimization_score`).
  * `allocation_explanation`: Driver and component breakdown (`primary_driver`, `score_components` with `base_score`, `marginal_score`, `equity_bonus`, `risk_penalty`).
* **Portfolio Metrics**: `total_predicted_impact`, `average_saturation`, `underserved_region_allocation_share`.
* **`portfolio_breakdown`**: Detailed explainability metadata dictionary:
  * `budget_utilization`, `project_count_funded`, `state_allocation_distribution`, `sector_allocation_distribution`, `average_base_score`, `average_marginal_score`, `average_saturation`.
* **`optimization_audit`**: High-level execution accounting audit:
  * `total_projects_considered`, `projects_funded`, `projects_skipped`, `budget_requested_total_paise`, `budget_allocated_total_paise`, `budget_unallocated_paise`.
* **`calculation_versions`**: Mapping of exact algorithm versions applied (`project-v1`, `dna-v1`, `saturation-v1`, `marginal-v1`, `optimizer-v1`).
* **`created_at`**: Deterministic snapshot timestamp.

## 4. Version
* **Current Version**: `optimizer-v1`
* **Scoring Engine Version**: `scoring-v1`
* **Saturation Version**: `saturation-v1`
* **Marginal Version**: `marginal-v1`
* **Source DNA Schema Version**: `dna-v1`
* **Version History**:
  * `optimizer-v1`: Initial deterministic base scoring and full sequential constrained budget optimizer.

## 5. Assumptions
* Zero AI or Large Language Model calls are permitted within the optimizer.
* Financial units are strictly integer paise ($10,000,000\text{ paise} = \text{₹1 Lakh}$).
* When `require_full_budget_allocation = True`, `unallocated_paise` must be 0 unless constrained by mathematical impossibility.
* Same inputs + same weights + same constraints guarantee identical allocations and scores across all runtime environments.
* Output scores are mathematically bounded in $[0.0, 1.0]$ and rounded to 6 decimal places.
* No timestamps or hidden clocks inside optimization routines.

## 6. Future Formula Section
### Formula Implementation (optimizer-v1)

#### 1. Composite Optimization Score
$$\begin{aligned}
\text{Optimization Score} = \text{round}\Big(\text{clip}\big(
    & w_{\text{need}} \cdot \text{need\_score} \\
    & + w_{\text{marginal}} \cdot \text{marginal\_impact\_score} \\
    & + w_{\text{efficiency}} \cdot \text{cost\_efficiency\_score} \\
    & + w_{\text{evidence}} \cdot \text{evidence\_strength\_score} \\
    & + w_{\text{scalability}} \cdot \text{scalability\_score} \\
    & + w_{\text{equity}} \cdot (1.0 - \text{saturation\_index}) \\
    & - w_{\text{risk}} \cdot \text{implementation\_risk\_score},
    \, 0.0,\, 1.0\big),\, 6\Big)
\end{aligned}$$

#### 2. Deterministic 5-Step Tie-Breaking
1. Higher `optimization_score`
2. Higher `marginal_impact_score`
3. Lower `saturation_index`
4. Higher `need_score`
5. Lexicographical `project_id`

#### 3. Sequential Constrained Allocation
For each ranked candidate project:
$$\text{candidate} = \min(\text{remaining\_budget},\, \text{project\_cap\_remaining},\, \text{region\_cap\_remaining})$$
$$\text{allocated} = \text{apply\_minimum\_allocation}(\text{candidate},\, \text{constraints})$$

#### 4. Reason Code Rules
* `HIGH_NEED`: `need_score >= 0.80`
* `LOW_SATURATION`: `saturation_index <= 0.24`
* `HIGH_MARGINAL_IMPACT`: `marginal_impact_score >= 0.70`
* `HIGH_COST_EFFICIENCY`: `cost_efficiency_score >= 0.80`
* `STRONG_EVIDENCE`: `evidence_strength_score >= 0.80`
* `HIGH_SCALABILITY`: `scalability_score >= 0.80`
* `LOW_EVIDENCE`: `evidence_strength_score < 0.50`
* `HIGH_IMPLEMENTATION_RISK`: `implementation_risk_score >= 0.50`
* `HIGH_SATURATION`: `saturation_index >= 0.50`
* `BUDGET_CONSTRAINT`: Allocated amount limited by remaining budget.
* `REGIONAL_CAP`: Allocated amount limited by regional cap.
* `MINIMUM_ALLOCATION`: Limited or rejected by minimum allocation floor.
