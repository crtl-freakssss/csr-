import { useState, useEffect } from 'react';
import type { OptimizationResult, ApiError } from '../../types';
import { MOCK_OPTIMIZATION_RESULT } from '../../mocks';
import { Loader2, AlertCircle, LayoutList, CheckCircle2 } from 'lucide-react';

type State = 'LOADING' | 'SUCCESS' | 'ERROR' | 'EMPTY';

export default function Allocations() {
    const [state, setState] = useState<State>('LOADING');
    const [result, setResult] = useState<OptimizationResult | null>(null);
    const [error, _setError] = useState<ApiError | null>(null);

    useEffect(() => {
        // Simulate fetching the latest allocation result
        setTimeout(() => {
            setResult(MOCK_OPTIMIZATION_RESULT.data);
            setState('SUCCESS');
        }, 1000);
    }, []);

    if (state === 'LOADING') {
        return (
            <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-xl bg-surface-container-lowest p-space-xl shadow-sm">
                <Loader2 className="h-8 w-8 animate-spin text-secondary" />
                <p className="font-body-sm text-body-sm text-on-surface-variant">Fetching optimal allocations from Decision Engine...</p>
            </div>
        );
    }

    if (state === 'ERROR' && error) {
        return (
            <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-xl bg-surface-container-lowest p-space-xl shadow-sm border border-error/20">
                <AlertCircle className="h-10 w-10 text-error" />
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">Optimization Failed</h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md text-center">{error.error.message}</p>
                <code className="mt-2 rounded bg-surface-container-low px-2 py-1 font-mono text-[11px] text-on-surface-variant">Request ID: {error.error.request_id}</code>
            </div>
        );
    }

    if (state === 'EMPTY') {
        return (
            <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-xl bg-surface-container-lowest p-space-xl shadow-sm">
                <LayoutList className="h-10 w-10 text-on-surface-variant/50" />
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">No Allocations Found</h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant text-center max-w-md">Run the optimizer from the optimization configuration screen first to generate the portfolio frontier.</p>
            </div>
        );
    }

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header Hero */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg lg:p-space-xl shadow-sm">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 rounded-full bg-secondary-fixed/50 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <span className="h-2 w-2 animate-pulse rounded-full bg-secondary"></span>
                            <span>Decision Engine Result · Run #{result?.run_id || 'AL-XXXX'}</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Optimal Allocation for ₹{((result?.total_budget_paise || 0) / 100).toLocaleString()}
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            Algorithmic frontier generated across vetted programs. Linear programming solved subject to thematic allocations, constraints, and safeguards.
                            <span className="ml-2 rounded bg-surface-container px-1.5 py-0.5 font-label-caps text-[10px] uppercase text-on-surface-variant">DEMO DATA</span>
                        </p>
                    </div>
                </div>
                
                {/* Metrics Grid */}
                <div className="mt-space-xl grid grid-cols-2 gap-space-md rounded-xl bg-surface-container-low/70 p-space-md md:grid-cols-4">
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Total Capital Pool</span>
                        <span className="mt-0.5 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                            ₹{((result?.total_budget_paise || 0) / 100).toLocaleString()}
                        </span>
                        <span className="mt-1 flex items-center gap-1 font-label-md text-label-md font-medium text-secondary">
                            <CheckCircle2 className="h-3.5 w-3.5" /> 
                            {result?.total_budget_paise === result?.total_allocated_paise ? '100% Fully Allocated' : 'Partially Allocated'}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Programs Selected</span>
                        <span className="mt-0.5 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                            {result?.selected_projects_count}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Total Allocated</span>
                        <span className="mt-0.5 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                            ₹{((result?.total_allocated_paise || 0) / 100).toLocaleString()}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Expected Impact Aggregate</span>
                        <span className="mt-0.5 font-tabular-stat text-tabular-stat font-semibold text-secondary">
                            {result?.expected_impact_aggregate.toLocaleString()}
                        </span>
                        <span className="mt-1 font-label-md text-label-md text-on-surface-variant">Model output scale</span>
                    </div>
                </div>
            </div>

            {/* Allocations Table */}
            <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm">
                <div className="flex items-center justify-between pb-space-sm">
                    <div>
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Recommended Tranche Schedule</h2>
                        <p className="font-body-sm text-body-sm text-on-surface-variant">Ranked mathematically by marginal social impact yield.</p>
                    </div>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-left font-body-md text-body-md">
                        <thead>
                            <tr className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                                <th className="rounded-l px-space-md py-2.5">Program & NGO Partner</th>
                                <th className="px-space-md py-2.5">Sector & State</th>
                                <th className="px-space-sm py-2.5 text-right">Commitment</th>
                                <th className="px-space-md py-2.5">Targeted Social Returns</th>
                                <th className="rounded-r px-space-md py-2.5">Reason Codes</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-container-high/40">
                            {result?.allocations.map((alloc, index) => (
                                <tr key={alloc.project_id} className="transition-colors hover:bg-surface-container-low/50">
                                    <td className="px-space-md py-space-md align-top">
                                        <div className="flex items-start gap-space-xs">
                                            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-container text-[11px] font-bold text-on-primary-fixed-variant">
                                                {String(index + 1).padStart(2, '0')}
                                            </span>
                                            <div>
                                                <div className="font-headline-sm text-headline-sm font-semibold leading-tight text-on-surface">{alloc.project_name}</div>
                                                <div className="mt-0.5 font-body-sm text-body-sm text-on-surface-variant">{alloc.organization_name}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-space-md py-space-md align-top">
                                        <div className="font-label-md text-label-md font-semibold text-on-surface">{alloc.sector}</div>
                                        <div className="mt-0.5 font-body-sm text-body-sm text-on-surface-variant">{alloc.state}</div>
                                    </td>
                                    <td className="px-space-sm py-space-md align-top text-right font-tabular-stat text-headline-sm font-semibold text-on-surface">
                                        ₹{(alloc.allocated_amount_paise / 100).toLocaleString()}
                                    </td>
                                    <td className="px-space-md py-space-md align-top">
                                        <div className="font-label-md text-label-md font-semibold text-on-surface">Impact: {alloc.expected_impact_score}</div>
                                        <div className="mt-1 font-label-caps text-label-caps font-semibold text-secondary">Marginal: {alloc.marginal_impact_score}</div>
                                    </td>
                                    <td className="px-space-md py-space-md align-top">
                                        <div className="flex flex-wrap gap-1.5">
                                            {alloc.reason_codes.map((code) => (
                                                <span key={code} className="rounded bg-surface-container-high px-2 py-0.5 font-label-caps text-label-caps text-on-surface">
                                                    {code}
                                                </span>
                                            ))}
                                        </div>
                                        <div className="mt-2 font-body-sm text-body-sm text-on-surface-variant">Constraint: {alloc.constraint_status}</div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
