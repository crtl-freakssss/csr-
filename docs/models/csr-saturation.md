# CSR Saturation Model Specification

## 1. Purpose
The CSR Saturation Model deterministically measures the degree of corporate social responsibility (CSR) capital concentration within a target geographic area, demographic group, and thematic sector. Its primary role in AllocateAI is to ensure equitable fund distribution by identifying severely underserved regions (where new capital yields high marginal social value) versus heavily saturated pockets (where additional funding risks duplication or diminishing returns).

In Phase 3, the `SaturationEngine` (`saturation-v1`) deterministically computes a continuous `saturation_index` $\in [0.0, 1.0]$, an `estimated_beneficiary_coverage`, and a data `confidence` score for consumption by the Marginal Impact Engine and Budget Optimizer.

## 2. Inputs
The model ingests structured project and regional metadata:
* **`Project` Entity**:
  * `project_id`: Unique intervention identifier.
  * `beneficiary_profile.target_count`: Planned beneficiaries reached.
  * `impact_dna.need_score`: Need severity index ($\in [0.0, 1.0]$).
  * `impact_dna.beneficiary_reach`: Fallback reach parameter.
* **`SaturationContext` Entity**:
  * `state`: Target Indian state (e.g. "Bihar", "Maharashtra").
  * `sector`: Canonical `ProjectSector` enum (e.g., `EDUCATION`, `HEALTHCARE`).
  * `total_regional_csr_paise`: Aggregated active CSR capital deployed in integer paise ($ge 0$).
  * `total_population`: Census population of the region.
  * `target_population`: Sized demographic vulnerable target population.

## 3. Outputs
The model emits a validated `SaturationResult` conforming to Technical Contract v1.0:
* **`project_id`**: Associated project ID.
* **`state`**: Target state.
* **`sector`**: Target thematic sector.
* **`saturation_index`**: Normalized scalar value $\in [0.0, 1.0]$ representing capital density.
* **`need_score`**: Calibrated regional need score.
* **`existing_csr_amount_paise`**: Total existing CSR capital active in the regional cluster in integer paise.
* **`estimated_beneficiary_coverage`**: Portion of the target population reached ($\in [0.0, 1.0]$).
* **`confidence`**: Statistical confidence in the saturation assessment ($\in [0.0, 1.0]$).
* **`calculation_version`**: `"saturation-v1"`.
* **`component_breakdown`**: Dictionary of intermediate component scores and applied weights (`funding_density_score`, `beneficiary_coverage_score`, `need_adjustment_score`, and `weights`).

## 4. Version
* **Current Version**: `saturation-v1`
* **Model Name**: `csr-saturation-engine`
* **Schema Version**: `project-v1`
* **Version History**:
  * `saturation-v1`: Initial deterministic multi-component saturation engine with funding density, beneficiary coverage, and need adjustment.

## 5. Assumptions
* Financial accounting uses strictly integer paise without floating-point representation ($10,000,000\text{ paise} = \text{₹1 Lakh}$).
* Zero AI or Large Language Model calls are permitted.
* Pure mathematical evaluation: same inputs + same context guarantee identical outputs across all environments.
* The saturation index provides numeric guidance to the optimizer; categorical threshold labels are strictly for presentation.
* No system clocks or temporal dependencies in calculation logic.

## 6. Future Formula Section
### Formula Implementation (saturation-v1)
The saturation index is computed from three transparent, deterministic components:

1. **Funding Density Score** ($S_{\text{density}}$):
   $$\text{Benchmark Capacity (paise)} = \text{target\_population} \times 10,000,000\text{ paise (₹1,000 per capita)}$$
   $$S_{\text{density}} = \text{clip}\left(\frac{\text{total\_regional\_csr\_paise}}{\text{Benchmark Capacity}},\, 0.0,\, 1.0\right)$$

2. **Beneficiary Coverage Score** ($S_{\text{coverage}}$):
   $$S_{\text{coverage}} = \text{clip}\left(\frac{\text{beneficiaries\_reached}}{\text{target\_population}},\, 0.0,\, 1.0\right)$$

3. **Need Adjustment Score** ($S_{\text{need\_adj}}$):
   $$S_{\text{need\_adj}} = \text{clip}\left(1.0 - \text{need\_score},\, 0.0,\, 1.0\right)$$

### Canonical Combination
$$\text{saturation\_index} = \text{clip}\Big(0.40 \cdot S_{\text{density}} + 0.30 \cdot S_{\text{coverage}} + 0.30 \cdot S_{\text{need\_adj}},\, 0.0,\, 1.0\Big)$$

### Confidence Calculation
Evaluated across 4 data completeness factors (weighted $0.25$ each):
$$\text{confidence} = 0.25 \cdot c_{\text{pop}} + 0.25 \cdot c_{\text{funding}} + 0.25 \cdot c_{\text{beneficiaries}} + 0.25 \cdot c_{\text{need}}$$

### Presentation Interpretation Bands
Technical Contract Section 11 guidance:
* `0.00 – 0.24`: `VERY_LOW` (severely underserved, high equity priority)
* `0.25 – 0.37`: `LOW` (underserved)
* `0.38 – 0.49`: `MODERATE` (moderately funded)
* `0.50 – 0.74`: `HIGH` (approaching saturation)
* `0.75 – 1.00`: `VERY_HIGH` (heavily saturated, high risk of diminishing returns)
