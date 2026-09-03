import { useState } from 'react';
import type { OptimizationResult, ApiError } from '../../types';
import { MOCK_OPTIMIZATION_RESULT } from '../../mocks';
import { Loader2, AlertCircle, Settings2, Play, CheckCircle2 } from 'lucide-react';

type State = 'EMPTY' | 'LOADING' | 'SUCCESS' | 'ERROR';

export default function Optimization() {
    const [state, setState] = useState<State>('EMPTY');
    const [result, setResult] = useState<OptimizationResult | null>(null);
    const [error, setError] = useState<ApiError | null>(null);
    const [budget, setBudget] = useState(5000000); // 50 Lakhs default

    const handleRunOptimization = () => {
        setState('LOADING');
        setError(null);
        setResult(null);

        // Simulate API call to Decision Engine
        setTimeout(() => {
            setResult(MOCK_OPTIMIZATION_RESULT.data);
            setState('SUCCESS');
        }, 1500);
    };

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header Hero */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg lg:p-space-xl shadow-sm">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 rounded-full bg-secondary-fixed/50 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <span className="h-2 w-2 animate-pulse rounded-full bg-secondary"></span>
                            <span>DECISION ENGINE CONFIGURATION</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Budget Optimizer
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            Configure and run the deterministic decision-engine optimizer to find the highest marginal impact allocation across all verified proposals.
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-space-lg lg:grid-cols-3">
                {/* Controls */}
                <div className="space-y-space-lg rounded-xl bg-surface-container-lowest p-space-lg shadow-sm lg:col-span-1">
                    <div className="flex items-center gap-2">
                        <Settings2 className="h-5 w-5 text-secondary" />
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Configuration</h2>
                    </div>
                    
                    <div className="space-y-2">
                        <label className="block font-label-md text-label-md font-medium text-on-surface-variant">Total CSR Budget (INR)</label>
                        <input 
                            type="number" 
                            value={budget}
                            onChange={(e) => setBudget(Number(e.target.value))}
                            className="block w-full rounded-md border border-outline-variant/50 bg-surface-container-low px-space-sm py-2 font-body-md text-body-md text-on-surface placeholder-on-surface-variant/50 focus:border-secondary focus:outline-none focus:ring-1 focus:ring-secondary"
                        />
                    </div>

                    <div className="pt-space-sm">
                        <button
                            onClick={handleRunOptimization}
                            disabled={state === 'LOADING'}
                            className="flex w-full items-center justify-center gap-2 rounded bg-secondary px-space-md py-2.5 font-label-md text-label-md font-semibold text-on-secondary shadow-md transition-colors hover:bg-on-secondary-container disabled:opacity-50"
                        >
                            {state === 'LOADING' ? (
                                <Loader2 className="h-[18px] w-[18px] animate-spin" />
                            ) : (
                                <Play className="h-[18px] w-[18px] fill-current" />
                            )}
                            <span>{state === 'LOADING' ? 'Running Optimizer...' : 'Run Optimization'}</span>
                        </button>
                    </div>
                </div>

                {/* Results Area */}
                <div className="flex min-h-[300px] flex-col overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg shadow-sm lg:col-span-2">
                    {state === 'EMPTY' && (
                        <div className="flex h-full flex-col items-center justify-center space-y-4 text-center">
                            <Settings2 className="h-12 w-12 text-on-surface-variant/30" />
                            <div>
                                <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">Ready to Optimize</p>
                                <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">Configure your parameters and run the optimizer.</p>
                            </div>
                        </div>
                    )}

                    {state === 'LOADING' && (
                        <div className="flex h-full flex-col items-center justify-center space-y-4 text-center">
                            <Loader2 className="h-12 w-12 animate-spin text-secondary" />
                            <div>
                                <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">Decision Engine Running</p>
                                <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">Evaluating marginal impact across all proposals...</p>
                            </div>
                        </div>
                    )}

                    {state === 'ERROR' && error && (
                        <div className="flex h-full flex-col items-center justify-center space-y-4 text-center">
                            <AlertCircle className="h-12 w-12 text-error" />
                            <div>
                                <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">Optimization Failed</p>
                                <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">{error.error.message}</p>
                                <code className="mt-2 inline-block rounded bg-surface-container-low px-2 py-1 font-mono text-[11px] text-on-surface-variant">
                                    Error Code: {error.error.code}
                                </code>
                            </div>
                        </div>
                    )}

                    {state === 'SUCCESS' && result && (
                        <div className="flex h-full flex-col space-y-space-lg">
                            <div className="flex items-center justify-between border-b border-surface-container-high pb-space-sm">
                                <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Optimization Complete</h2>
                                <span className="rounded bg-surface-container-high px-1.5 py-0.5 font-label-caps text-[10px] uppercase text-on-surface-variant">DEMO DATA</span>
                            </div>
                            
                            <div className="grid grid-cols-1 gap-space-md sm:grid-cols-3">
                                <div className="rounded-lg bg-surface-container-low p-space-md">
                                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Total Allocated</p>
                                    <p className="mt-1 font-tabular-stat text-tabular-stat font-semibold text-on-surface">₹{(result.total_allocated_paise / 100).toLocaleString()}</p>
                                </div>
                                <div className="rounded-lg bg-surface-container-low p-space-md">
                                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Projects Selected</p>
                                    <p className="mt-1 font-tabular-stat text-tabular-stat font-semibold text-on-surface">{result.selected_projects_count}</p>
                                </div>
                                <div className="rounded-lg bg-surface-container-low p-space-md">
                                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Expected Impact</p>
                                    <p className="mt-1 font-tabular-stat text-tabular-stat font-semibold text-secondary">{result.expected_impact_aggregate.toLocaleString()}</p>
                                </div>
                            </div>
                            
                            <div className="mt-auto pt-space-lg font-body-sm text-body-sm text-on-surface-variant">
                                <p className="flex items-center gap-2">
                                    <CheckCircle2 className="h-4 w-4 text-secondary" />
                                    Successfully generated frontier with Run ID: <span className="font-mono text-on-surface">{result.run_id}</span>
                                </p>
                                <p className="mt-4">
                                    View the detailed recommended tranche schedule in the <a href="/allocations" className="font-semibold text-secondary hover:underline">Allocations</a> view.
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
