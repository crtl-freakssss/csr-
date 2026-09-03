import { useState, useEffect } from 'react';
import type { ExplainabilityResult, ApiError } from '../../types';
import { MOCK_EXPLAINABILITY_RESULT } from '../../mocks';
import { Loader2, AlertCircle, HelpCircle, Eye, CheckCircle2 } from 'lucide-react';

type State = 'LOADING' | 'SUCCESS' | 'ERROR' | 'EMPTY';

export default function Explainability() {
    const [state, setState] = useState<State>('LOADING');
    const [result, setResult] = useState<ExplainabilityResult | null>(null);
    const [error, _setError] = useState<ApiError | null>(null);

    useEffect(() => {
        // Simulate fetching explanation for a specific project allocation
        setTimeout(() => {
            setResult(MOCK_EXPLAINABILITY_RESULT.data);
            setState('SUCCESS');
        }, 1000);
    }, []);

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    TRANSPARENCY
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    Why this decision?
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    The system explains the decision; it does not hide the decision behind AI.
                </p>
                {state === 'SUCCESS' && (
                    <div className="mt-4 inline-flex items-center space-x-2 rounded-full bg-[#f59e0b]/10 px-3 py-1 font-label-md text-sm text-[#f59e0b]">
                        <span>DEMO DATA</span>
                    </div>
                )}
            </div>

            {state === 'LOADING' && (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest shadow-sm">
                    <Loader2 className="h-8 w-8 animate-spin text-secondary" />
                    <p className="font-body-md text-body-md text-on-surface-variant">Generating explanation from decision engine metadata...</p>
                </div>
            )}

            {state === 'ERROR' && error && (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest shadow-sm">
                    <AlertCircle className="h-8 w-8 text-[#ba1a1a]" />
                    <p className="font-headline-sm text-headline-sm font-semibold text-[#ba1a1a]">Failed to load explanation</p>
                    <p className="font-body-md text-body-md text-on-surface-variant">{error.error.message}</p>
                </div>
            )}

            {state === 'EMPTY' && (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest shadow-sm">
                    <HelpCircle className="h-8 w-8 text-on-surface-variant" />
                    <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">No Project Selected</p>
                    <p className="font-body-md text-body-md text-on-surface-variant">Select a project allocation to view its explanation.</p>
                </div>
            )}

            {state === 'SUCCESS' && result && (
                <div className="grid grid-cols-1 gap-space-lg lg:grid-cols-3">
                    
                    {/* Left Column - Details */}
                    <div className="space-y-space-lg lg:col-span-1">
                        <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">
                            <h2 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">Allocation Details</h2>
                            <div className="space-y-4">
                                <div>
                                    <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Allocation Amount</p>
                                    <p className="font-tabular-stat text-tabular-stat font-semibold text-on-surface">₹{(result.allocation_amount_paise / 100).toLocaleString()}</p>
                                </div>
                                <div>
                                    <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Base Score</p>
                                    <p className="font-tabular-stat text-tabular-stat font-semibold text-on-surface">{result.base_score}</p>
                                </div>
                                <div>
                                    <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Rank in Sector</p>
                                    <p className="font-tabular-stat text-tabular-stat font-semibold text-on-surface">#{result.rank}</p>
                                </div>
                            </div>
                        </div>

                        <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">
                            <h2 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">Reason Codes</h2>
                            <div className="flex flex-wrap gap-2">
                                {result.reason_codes.map((code) => (
                                    <span key={code} className="rounded border border-outline-variant/50 bg-surface-container-low px-2 py-1 font-mono text-xs text-on-surface-variant">
                                        {code}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">
                            <h2 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">Constraints Applied</h2>
                            <ul className="space-y-2">
                                {result.applied_constraints.map((constraint, idx) => (
                                    <li key={idx} className="flex items-center space-x-2 font-body-md text-sm text-secondary">
                                        <CheckCircle2 className="h-4 w-4 shrink-0" />
                                        <span>{constraint}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    {/* Right Column - Contributions */}
                    <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm lg:col-span-2">
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface mb-6">Score Contributions</h2>
                        
                        <div className="space-y-6">
                            {Object.entries(result.contributions).map(([key, value]) => {
                                const isPositive = value >= 0;
                                const widthPercentage = Math.min(Math.abs(value) * 100 * 2, 100);
                                return (
                                    <div key={key} className="space-y-2">
                                        <div className="flex justify-between font-body-md text-sm">
                                            <span className="capitalize text-on-surface">{key.replace('_', ' ')}</span>
                                            <span className={isPositive ? 'text-secondary font-semibold' : 'text-[#ba1a1a] font-semibold'}>
                                                {isPositive ? '+' : ''}{value.toFixed(2)}
                                            </span>
                                        </div>
                                        <div className="relative flex h-2 w-full items-center bg-surface-container-high rounded-full overflow-hidden">
                                            <div 
                                                className={`absolute h-full rounded-full ${isPositive ? 'bg-secondary' : 'bg-[#ba1a1a]'}`}
                                                style={{ width: `${widthPercentage}%` }}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        
                        <div className="mt-12 rounded-lg bg-surface-container-low p-4 border border-outline-variant/30">
                            <div className="flex items-start space-x-3">
                                <Eye className="h-5 w-5 shrink-0 text-on-surface-variant mt-0.5" />
                                <div>
                                    <p className="font-label-md text-sm font-semibold text-on-surface">Model Lineage</p>
                                    <div className="mt-2 font-mono text-xs text-on-surface-variant space-y-1">
                                        <p>Optimizer: {result.model_versions.optimizer}</p>
                                        <p>Marginal Impact: {result.model_versions.marginal_impact}</p>
                                        <p>Saturation: {result.model_versions.saturation}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
