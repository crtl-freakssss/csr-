export interface ApiResponse<T> {
    data: T;
    meta: {
        request_id: string;
        timestamp: string;
        schema_version: string;
    };
}

export interface ApiError {
    error: {
        code: string;
        message: string;
        details?: any;
        request_id: string;
    };
}

export type ReasonCode =
    | 'HIGH_NEED'
    | 'LOW_SATURATION'
    | 'HIGH_MARGINAL_IMPACT'
    | 'HIGH_COST_EFFICIENCY'
    | 'STRONG_EVIDENCE'
    | 'HIGH_SCALABILITY'
    | 'HIGH_IMPLEMENTATION_RISK'
    | 'LOW_EVIDENCE'
    | 'HIGH_SATURATION'
    | 'BUDGET_CONSTRAINT'
    | 'REGIONAL_CAP'
    | 'MINIMUM_ALLOCATION'
    | 'MISSING_DATA'
    | 'DUE_DILIGENCE_FLAG';

export interface Project {
    id: string;
    name: string;
    organization_id: string;
    organization_name: string;
    state: string;
    district?: string;
    sector: string;
    requested_amount_paise: number;
}

export interface Proposal {
    id: string;
    project_id: string;
    pdf_url: string;
    extraction_status: 'PENDING' | 'EXTRACTED' | 'FAILED';
    extracted_data?: Record<string, any>;
}

export interface ImpactDNA {
    project_id: string;
    need_score: number;
    expected_impact_score: number;
    cost_efficiency_score: number;
    evidence_strength_score: number;
    scalability_score: number;
    implementation_risk_score: number;
}

export interface SaturationResult {
    region: string;
    sector: string;
    saturation_index: number;
    need_index: number;
    existing_funding_paise: number;
    beneficiary_coverage_percent: number;
    confidence_score: number;
}

export interface MarginalImpactResult {
    project_id: string;
    total_impact_score: number;
    marginal_impact_score: number;
    additional_beneficiaries_per_lakh: number;
}

export interface OptimizationRequest {
    total_budget_paise: number;
    weights: {
        need: number;
        marginal_impact: number;
        saturation: number;
        cost_efficiency: number;
        evidence: number;
        risk: number;
    };
    constraints: {
        regional_cap_paise?: Record<string, number>;
        sector_cap_paise?: Record<string, number>;
        minimum_allocation_paise?: number;
    };
}

export interface Allocation {
    project_id: string;
    project_name: string;
    organization_name: string;
    state: string;
    sector: string;
    allocated_amount_paise: number;
    expected_impact_score: number;
    marginal_impact_score: number;
    reason_codes: ReasonCode[];
    constraint_status: string;
}

export interface OptimizationResult {
    run_id: string;
    total_budget_paise: number;
    total_allocated_paise: number;
    selected_projects_count: number;
    expected_impact_aggregate: number;
    allocations: Allocation[];
}

export interface ReallocationRequest {
    current_allocations: Allocation[];
    performance_updates: Record<string, any>;
}

export interface ReallocationDecision {
    project_id: string;
    project_name: string;
    amount_moved_paise: number;
    from_project_id?: string;
    to_project_id?: string;
    reason_codes: ReasonCode[];
    old_marginal_impact: number;
    new_marginal_impact: number;
}

export interface ReallocationResult {
    run_id: string;
    decisions: ReallocationDecision[];
    impact_change: number;
    saturation_change: number;
}

export interface DueDiligenceReport {
    ngo_id: string;
    ngo_name: string;
    overall_status: 'CLEAR' | 'REVIEW_REQUIRED' | 'FLAGGED';
    indicators: {
        registration_valid: boolean;
        financial_health_score: number;
        governance_score: number;
        compliance_score: number;
    };
    risk_flags: string[];
    evidence_quality_score: number;
    last_checked_at: string;
}

export interface AuditEvent {
    run_id: string;
    timestamp: string;
    event_type: 'OPTIMIZATION' | 'REALLOCATION' | 'MANUAL_OVERRIDE';
    budget_paise: number;
    weights_snapshot: Record<string, number>;
    constraints_snapshot: Record<string, any>;
    model_versions: {
        optimizer: string;
        marginal_impact: string;
        saturation: string;
    };
    status: 'SUCCESS' | 'FAILED';
}

export interface ExplainabilityResult {
    project_id: string;
    allocation_amount_paise: number;
    rank: number;
    base_score: number;
    contributions: {
        need: number;
        marginal_impact: number;
        saturation: number;
        cost_efficiency: number;
        evidence: number;
        risk: number;
    };
    reason_codes: ReasonCode[];
    applied_constraints: string[];
    model_versions: {
        optimizer: string;
        marginal_impact: string;
        saturation: string;
    };
}
