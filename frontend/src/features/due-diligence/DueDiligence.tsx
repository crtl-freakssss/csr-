import { useState } from 'react';
import type { DueDiligenceReport, ApiError } from '../../types';
import { MOCK_DUE_DILIGENCE_REPORT } from '../../mocks';
import { Loader2, AlertCircle, ShieldAlert, Search, ShieldCheck, Shield } from 'lucide-react';

type State = 'EMPTY' | 'LOADING' | 'SUCCESS' | 'ERROR';

export default function DueDiligence() {
    const [state, setState] = useState<State>('EMPTY');
    const [result, setResult] = useState<DueDiligenceReport | null>(null);
    const [error, setError] = useState<ApiError | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    const handleSearch = () => {
        if (!searchQuery.trim()) return;
        setState('LOADING');
        setError(null);
        setResult(null);

        // Simulate API call to check NGO
        setTimeout(() => {
            setResult(MOCK_DUE_DILIGENCE_REPORT.data);
            setState('SUCCESS');
        }, 1200);
    };

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    COMPLIANCE & RISK
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    NGO Due Diligence
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    AI-assisted due diligence and risk indicators based on available evidence.
                </p>
                <div className="mt-4 inline-flex items-center space-x-2 rounded-full bg-secondary/10 px-3 py-1 font-label-md text-sm text-secondary">
                    <Shield className="h-4 w-4" />
                    <span>Evidence requiring review. Does not represent legal verification.</span>
                </div>
            </div>

            {/* Search Bar */}
            <div className="flex space-x-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-space-lg shadow-sm">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-on-surface-variant" />
                    <input
                        type="text"
                        placeholder="Search NGO by name or registration ID..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className="block w-full rounded border border-outline-variant bg-surface-container-low py-2 pl-10 pr-3 font-body-md text-sm text-on-surface placeholder-on-surface-variant/50 focus:border-secondary focus:outline-none focus:ring-1 focus:ring-secondary"
                    />
                </div>
                <button
                    onClick={handleSearch}
                    disabled={state === 'LOADING' || !searchQuery.trim()}
                    className="flex items-center space-x-2 rounded bg-secondary px-6 py-2 font-label-md text-sm font-semibold text-on-secondary shadow-sm transition hover:bg-on-secondary-container disabled:opacity-50"
                >
                    {state === 'LOADING' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                    <span>Search</span>
                </button>
            </div>

            {/* States */}
            <div className="min-h-[400px]">
                {state === 'EMPTY' && (
                    <div className="flex h-full flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-12 text-center shadow-sm">
                        <Shield className="h-12 w-12 text-on-surface-variant" />
                        <div>
                            <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">Search an NGO to begin</p>
                            <p className="mt-1 font-body-md text-body-md text-on-surface-variant">Enter an NGO name or ID to view risk indicators and compliance status.</p>
                        </div>
                    </div>
                )}

                {state === 'LOADING' && (
                    <div className="flex h-full flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-12 text-center shadow-sm">
                        <Loader2 className="h-12 w-12 animate-spin text-secondary" />
                        <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">Running AI-Assisted Checks...</p>
                        <p className="font-body-md text-body-md text-on-surface-variant">Analyzing financial and governance records.</p>
                    </div>
                )}

                {state === 'ERROR' && error && (
                    <div className="flex h-full flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-12 text-center shadow-sm">
                        <AlertCircle className="h-12 w-12 text-[#ba1a1a]" />
                        <p className="font-headline-sm text-headline-sm font-semibold text-[#ba1a1a]">Due Diligence Check Failed</p>
                        <p className="font-body-md text-body-md text-on-surface-variant">{error.error.message}</p>
                    </div>
                )}

                {state === 'SUCCESS' && result && (
                    <div className="space-y-space-lg">
                        <div className="flex items-center justify-between">
                            <h2 className="font-headline-md text-headline-md font-semibold text-on-surface">{result.ngo_name}</h2>
                            <span className="rounded bg-[#f59e0b]/10 px-3 py-1 font-label-caps text-[10px] uppercase font-medium text-[#f59e0b]">
                                DEMO DATA
                            </span>
                        </div>

                        {/* Status Banner */}
                        <div className={`flex items-center space-x-3 rounded-lg border p-4 ${
                            result.overall_status === 'CLEAR' ? 'border-green-500/30 bg-green-500/10' :
                            result.overall_status === 'REVIEW_REQUIRED' ? 'border-[#f59e0b]/30 bg-[#f59e0b]/10' :
                            'border-[#ba1a1a]/30 bg-[#ba1a1a]/10'
                        }`}>
                            {result.overall_status === 'CLEAR' ? <ShieldCheck className="h-6 w-6 text-green-600" /> : <ShieldAlert className={`h-6 w-6 ${result.overall_status === 'REVIEW_REQUIRED' ? 'text-[#f59e0b]' : 'text-[#ba1a1a]'}`} />}
                            <div>
                                <p className={`font-semibold ${
                                    result.overall_status === 'CLEAR' ? 'text-green-700' :
                                    result.overall_status === 'REVIEW_REQUIRED' ? 'text-[#f59e0b]' :
                                    'text-[#ba1a1a]'
                                }`}>
                                    Status: {result.overall_status.replace('_', ' ')}
                                </p>
                                <p className="font-body-sm text-body-sm text-on-surface-variant">Last checked: {new Date(result.last_checked_at).toLocaleDateString()}</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 gap-space-lg md:grid-cols-2">
                            {/* Indicators */}
                            <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">
                                <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">Risk Indicators</h3>
                                <div className="space-y-4">
                                    <div className="flex justify-between">
                                        <span className="font-body-md text-body-md text-on-surface-variant">Registration Valid</span>
                                        <span className={`font-label-md text-sm font-semibold ${result.indicators.registration_valid ? 'text-secondary' : 'text-[#ba1a1a]'}`}>
                                            {result.indicators.registration_valid ? 'Yes' : 'No'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="font-body-md text-body-md text-on-surface-variant">Financial Health Score</span>
                                        <span className="font-label-md text-sm font-semibold text-on-surface">{(result.indicators.financial_health_score * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="font-body-md text-body-md text-on-surface-variant">Governance Score</span>
                                        <span className="font-label-md text-sm font-semibold text-on-surface">{(result.indicators.governance_score * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="font-body-md text-body-md text-on-surface-variant">Compliance Score</span>
                                        <span className="font-label-md text-sm font-semibold text-on-surface">{(result.indicators.compliance_score * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="flex justify-between border-t border-outline-variant/30 pt-4 mt-2">
                                        <span className="font-body-md text-body-md text-on-surface-variant">Evidence Quality / Confidence</span>
                                        <span className="font-label-md text-sm font-semibold text-on-surface">{(result.evidence_quality_score * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                            </div>

                            {/* Flags */}
                            <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">
                                <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">Identified Flags</h3>
                                {result.risk_flags.length > 0 ? (
                                    <ul className="space-y-3">
                                        {result.risk_flags.map((flag, idx) => (
                                            <li key={idx} className="flex items-start space-x-2 font-body-md text-sm text-[#f59e0b]">
                                                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                                                <span>{flag}</span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="font-body-md text-sm text-secondary flex items-center space-x-2">
                                        <ShieldCheck className="h-4 w-4" />
                                        <span>No flags identified.</span>
                                    </p>
                                )}
                                <div className="mt-8">
                                    <button className="font-label-md text-sm text-secondary hover:text-on-secondary-container transition-colors hover:underline">View supporting evidence →</button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
