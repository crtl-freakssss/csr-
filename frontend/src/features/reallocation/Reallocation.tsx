import { useState, useEffect } from 'react';
import type { ReallocationResult, ApiError } from '../../types';
import { MOCK_REALLOCATION_RESULT } from '../../mocks';
import { Loader2, AlertCircle, ArrowRightLeft, CheckCircle2 } from 'lucide-react';

type State = 'LOADING' | 'SUCCESS' | 'ERROR' | 'EMPTY';

export default function Reallocation() {
    const [state, setState] = useState<State>('LOADING');
    const [result, setResult] = useState<ReallocationResult | null>(null);
    const [error, _setError] = useState<ApiError | null>(null);

    useEffect(() => {
        // Simulate checking for reallocation opportunities
        setTimeout(() => {
            setResult(MOCK_REALLOCATION_RESULT.data);
            setState('SUCCESS');
        }, 1200);
    }, []);

    const handleApplyReallocation = () => {
        setState('LOADING');
        // Simulate applying it via API
        setTimeout(() => {
            setState('EMPTY');
        }, 1000);
    };

    if (state === 'LOADING') {
        return (
            <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-xl bg-surface-container-lowest p-space-xl shadow-sm">
                <Loader2 className="h-8 w-8 animate-spin text-secondary" />
                <p className="font-body-sm text-body-sm text-on-surface-variant">Analyzing performance and saturation metrics...</p>
            </div>
        );
    }

    if (state === 'ERROR' && error) {
        return (
            <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-xl bg-surface-container-lowest p-space-xl shadow-sm border border-error/20">
                <AlertCircle className="h-10 w-10 text-error" />
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">Reallocation Check Failed</h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md text-center">{error.error.message}</p>
                <code className="mt-2 rounded bg-surface-container-low px-2 py-1 font-mono text-[11px] text-on-surface-variant">Request ID: {error.error.request_id}</code>
            </div>
        );
    }

    if (state === 'EMPTY') {
        return (
            <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-xl bg-surface-container-lowest p-space-xl shadow-sm">
                <ArrowRightLeft className="h-10 w-10 text-on-surface-variant/50" />
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">No Reallocation Needed</h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant text-center max-w-md">Current allocations are optimally aligned with latest metrics.</p>
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
                            <span>DECISION ENGINE RESULT</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Dynamic Reallocation
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            Review and apply reallocation decisions recommended by the backend when project performance or saturation changes.
                            <span className="ml-2 rounded bg-surface-container px-1.5 py-0.5 font-label-caps text-[10px] uppercase text-on-surface-variant">DEMO DATA</span>
                        </p>
                    </div>
                </div>
                
                {/* Metrics Grid */}
                <div className="mt-space-xl grid grid-cols-2 gap-space-md rounded-xl bg-surface-container-low/70 p-space-md md:grid-cols-2">
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Expected Impact Change</span>
                        <span className={`mt-0.5 font-tabular-stat text-tabular-stat font-semibold ${result?.impact_change && result.impact_change > 0 ? 'text-secondary' : 'text-error'}`}>
                            {result?.impact_change && result.impact_change > 0 ? '+' : ''}{result?.impact_change}
                        </span>
                        <span className="mt-1 flex items-center gap-1 font-label-md text-label-md font-medium text-on-surface-variant">
                            <CheckCircle2 className="h-3.5 w-3.5 text-secondary" /> 
                            Marginal impact optimization
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Saturation Change</span>
                        <span className={`mt-0.5 font-tabular-stat text-tabular-stat font-semibold ${result?.saturation_change && result.saturation_change < 0 ? 'text-secondary' : 'text-on-surface'}`}>
                            {result?.saturation_change && result.saturation_change > 0 ? '+' : ''}{result?.saturation_change}
                        </span>
                    </div>
                </div>
            </div>

            {/* Decisions Table */}
            <div className="rounded-xl bg-surface-container-lowest shadow-sm">
                <div className="border-b border-surface-container-high px-space-md py-space-sm flex justify-between items-center">
                    <div>
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Recommended Movements</h2>
                    </div>
                    <button
                        onClick={handleApplyReallocation}
                        className="rounded bg-secondary px-4 py-2 font-label-md text-label-md font-semibold text-on-secondary shadow-md hover:bg-on-secondary-container transition-colors"
                    >
                        Apply Reallocation
                    </button>
                </div>
                
                <div className="overflow-x-auto p-space-md">
                    <table className="w-full text-left font-body-md text-body-md">
                        <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            <tr>
                                <th className="rounded-l px-space-md py-2.5">Project</th>
                                <th className="px-space-md py-2.5">Amount Moved (INR)</th>
                                <th className="px-space-sm py-2.5">From / To</th>
                                <th className="px-space-md py-2.5">Marginal Impact (Before → After)</th>
                                <th className="rounded-r px-space-md py-2.5">Reason Codes</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-container-high/40">
                            {result?.decisions.map((decision, idx) => (
                                <tr key={idx} className="transition-colors hover:bg-surface-container-low/50">
                                    <td className="px-space-md py-space-md align-top">
                                        <div className="font-headline-sm text-headline-sm font-semibold text-on-surface">{decision.project_name}</div>
                                    </td>
                                    <td className={`px-space-md py-space-md align-top font-tabular-stat text-headline-sm font-semibold ${decision.amount_moved_paise > 0 ? 'text-secondary' : 'text-error'}`}>
                                        {decision.amount_moved_paise > 0 ? '+' : '-'}₹{Math.abs(decision.amount_moved_paise / 100).toLocaleString()}
                                    </td>
                                    <td className="px-space-sm py-space-md align-top">
                                        <div className="flex flex-col gap-1">
                                            {decision.from_project_id && <span className="font-label-md text-label-md text-error bg-error/10 px-2 py-0.5 rounded-sm w-fit">From: {decision.from_project_id}</span>}
                                            {decision.to_project_id && <span className="font-label-md text-label-md text-secondary bg-secondary/10 px-2 py-0.5 rounded-sm w-fit">To: {decision.to_project_id}</span>}
                                        </div>
                                    </td>
                                    <td className="px-space-md py-space-md align-top">
                                        <div className="flex items-center gap-2 font-tabular-stat text-headline-sm text-on-surface">
                                            <span className="text-on-surface-variant">{decision.old_marginal_impact}</span>
                                            <ArrowRightLeft className="h-4 w-4 text-on-surface-variant/50" />
                                            <span className="font-semibold">{decision.new_marginal_impact}</span>
                                        </div>
                                    </td>
                                    <td className="px-space-md py-space-md align-top">
                                        <div className="flex flex-wrap gap-1.5">
                                            {decision.reason_codes.map((code) => (
                                                <span key={code} className="rounded bg-surface-container-high px-2 py-0.5 font-label-caps text-label-caps text-on-surface">
                                                    {code}
                                                </span>
                                            ))}
                                        </div>
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
