import type { 
    OptimizationResult, 
    ReallocationResult, 
    DueDiligenceReport, 
    ExplainabilityResult, 
    AuditEvent,
    ApiResponse,
    ApiError
} from '../types';

const meta = {
    request_id: 'req_mock_123',
    timestamp: new Date().toISOString(),
    schema_version: 'v1.0'
};

export const MOCK_API_ERROR: ApiError = {
    error: {
        code: 'DECISION_ENGINE_UNAVAILABLE',
        message: 'The backend decision engine is currently offline.',
        details: 'Failed to connect to the optimization service.',
        request_id: 'req_err_123'
    }
};

export const MOCK_OPTIMIZATION_RESULT: ApiResponse<OptimizationResult> = {
    data: {
        run_id: 'run_opt_001_DEMO',
        total_budget_paise: 500000000,
        total_allocated_paise: 480000000,
        selected_projects_count: 3,
        expected_impact_aggregate: 0.88,
        allocations: [
            {
                project_id: 'proj_1',
                project_name: 'DEMO DATA: Rural Learning Initiative',
                organization_name: 'ABC Foundation',
                state: 'Bihar',
                sector: 'Education',
                allocated_amount_paise: 250000000,
                expected_impact_score: 0.91,
                marginal_impact_score: 0.82,
                reason_codes: ['HIGH_NEED', 'HIGH_MARGINAL_IMPACT', 'STRONG_EVIDENCE'],
                constraint_status: 'Regional cap not exceeded'
            },
            {
                project_id: 'proj_2',
                project_name: 'DEMO DATA: Mobile Healthcare Program',
                organization_name: 'Health For All',
                state: 'Rajasthan',
                sector: 'Healthcare',
                allocated_amount_paise: 150000000,
                expected_impact_score: 0.86,
                marginal_impact_score: 0.78,
                reason_codes: ['HIGH_NEED', 'HIGH_COST_EFFICIENCY'],
                constraint_status: 'Sector cap not exceeded'
            },
            {
                project_id: 'proj_3',
                project_name: 'DEMO DATA: Women Skills Initiative',
                organization_name: 'Empower Foundation',
                state: 'Jharkhand',
                sector: 'Livelihood',
                allocated_amount_paise: 80000000,
                expected_impact_score: 0.82,
                marginal_impact_score: 0.75,
                reason_codes: ['LOW_SATURATION', 'HIGH_SCALABILITY'],
                constraint_status: 'Minimum allocation met'
            }
        ]
    },
    meta
};

export const MOCK_REALLOCATION_RESULT: ApiResponse<ReallocationResult> = {
    data: {
        run_id: 'run_realloc_001_DEMO',
        impact_change: +0.05,
        saturation_change: -0.02,
        decisions: [
            {
                project_id: 'proj_1',
                project_name: 'DEMO DATA: Rural Learning Initiative',
                amount_moved_paise: -11500000,
                to_project_id: 'proj_2',
                reason_codes: ['HIGH_SATURATION'],
                old_marginal_impact: 0.82,
                new_marginal_impact: 0.79
            },
            {
                project_id: 'proj_2',
                project_name: 'DEMO DATA: Mobile Healthcare Program',
                amount_moved_paise: 11500000,
                from_project_id: 'proj_1',
                reason_codes: ['HIGH_MARGINAL_IMPACT'],
                old_marginal_impact: 0.78,
                new_marginal_impact: 0.85
            }
        ]
    },
    meta
};

export const MOCK_DUE_DILIGENCE_REPORT: ApiResponse<DueDiligenceReport> = {
    data: {
        ngo_id: 'org_1',
        ngo_name: 'DEMO DATA: ABC Foundation',
        overall_status: 'REVIEW_REQUIRED',
        indicators: {
            registration_valid: true,
            financial_health_score: 0.85,
            governance_score: 0.70,
            compliance_score: 0.90
        },
        risk_flags: ['Missing recent FCRA renewal documentation'],
        evidence_quality_score: 0.65,
        last_checked_at: new Date().toISOString()
    },
    meta
};

export const MOCK_EXPLAINABILITY_RESULT: ApiResponse<ExplainabilityResult> = {
    data: {
        project_id: 'proj_1',
        allocation_amount_paise: 250000000,
        rank: 1,
        base_score: 0.91,
        contributions: {
            need: 0.35,
            marginal_impact: 0.25,
            saturation: 0.15,
            cost_efficiency: 0.10,
            evidence: 0.10,
            risk: -0.04
        },
        reason_codes: ['HIGH_NEED', 'HIGH_MARGINAL_IMPACT', 'STRONG_EVIDENCE'],
        applied_constraints: ['Regional cap not exceeded'],
        model_versions: {
            optimizer: 'optimizer-v1',
            marginal_impact: 'marginal-v1',
            saturation: 'saturation-v1'
        }
    },
    meta
};

export const MOCK_AUDIT_EVENTS: ApiResponse<AuditEvent[]> = {
    data: [
        {
            run_id: 'run_opt_001_DEMO',
            timestamp: new Date().toISOString(),
            event_type: 'OPTIMIZATION',
            budget_paise: 500000000,
            weights_snapshot: { need: 0.3, marginal_impact: 0.3, saturation: 0.2, risk: 0.2 },
            constraints_snapshot: { minimum_allocation_paise: 1000000 },
            model_versions: {
                optimizer: 'optimizer-v1',
                marginal_impact: 'marginal-v1',
                saturation: 'saturation-v1'
            },
            status: 'SUCCESS'
        },
        {
            run_id: 'run_opt_002_DEMO',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            event_type: 'OPTIMIZATION',
            budget_paise: 300000000,
            weights_snapshot: { need: 0.4, marginal_impact: 0.2, saturation: 0.2, risk: 0.2 },
            constraints_snapshot: {},
            model_versions: {
                optimizer: 'optimizer-v1',
                marginal_impact: 'marginal-v1',
                saturation: 'saturation-v1'
            },
            status: 'FAILED'
        }
    ],
    meta
};
