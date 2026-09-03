import React, { useState, useEffect } from 'react';
import type { AuditEvent, ApiError } from '../../types';
import { MOCK_AUDIT_EVENTS } from '../../mocks';
import { Loader2, AlertCircle, FileSearch, Calendar, ChevronDown, CheckCircle2, XCircle } from 'lucide-react';

type State = 'LOADING' | 'SUCCESS' | 'ERROR' | 'EMPTY';

export default function Audit() {
    const [state, setState] = useState<State>('LOADING');
    const [events, setEvents] = useState<AuditEvent[]>([]);
    const [error, _setError] = useState<ApiError | null>(null);
    const [expandedRow, setExpandedRow] = useState<string | null>(null);

    useEffect(() => {
        // Simulate fetching audit log
        setTimeout(() => {
            setEvents(MOCK_AUDIT_EVENTS.data);
            setState('SUCCESS');
        }, 1200);
    }, []);

    const toggleRow = (runId: string) => {
        setExpandedRow(expandedRow === runId ? null : runId);
    };

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    COMPLIANCE & TRACEABILITY
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    Audit & History
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    System is auditable and reproducible. Review past decision engine runs and overrides.
                </p>
                {state === 'SUCCESS' && (
                    <div className="mt-4 inline-flex items-center space-x-2 rounded-full bg-[#f59e0b]/10 px-3 py-1 font-label-md text-sm text-[#f59e0b]">
                        <span>DEMO DATA</span>
                    </div>
                )}
            </div>

            {state === 'LOADING' && (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest shadow-sm">
                    <Loader2 className="h-8 w-8 animate-spin text-on-surface-variant" />
                    <p className="font-body-md text-body-md text-on-surface-variant">Loading audit history...</p>
                </div>
            )}

            {state === 'ERROR' && error && (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest shadow-sm">
                    <AlertCircle className="h-8 w-8 text-[#ba1a1a]" />
                    <p className="font-headline-sm text-headline-sm font-semibold text-[#ba1a1a]">Failed to load audit events</p>
                    <p className="font-body-md text-body-md text-on-surface-variant">{error.error.message}</p>
                </div>
            )}

            {state === 'EMPTY' && (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest shadow-sm">
                    <FileSearch className="h-8 w-8 text-on-surface-variant" />
                    <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">No Audit History Found</p>
                </div>
            )}

            {state === 'SUCCESS' && events.length > 0 && (
                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest shadow-sm overflow-hidden">
                    <table className="w-full text-left font-body-md text-body-md">
                        <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant border-b border-outline-variant/30">
                            <tr>
                                <th className="px-space-md py-3 w-12"></th>
                                <th className="px-space-md py-3">Timestamp</th>
                                <th className="px-space-md py-3">Run ID</th>
                                <th className="px-space-md py-3">Event Type</th>
                                <th className="px-space-md py-3">Budget (INR)</th>
                                <th className="px-space-md py-3">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {events.map((evt) => (
                                <React.Fragment key={evt.run_id}>
                                    <tr 
                                        className="border-b border-outline-variant/20 cursor-pointer hover:bg-surface-container-low/50 transition-colors"
                                        onClick={() => toggleRow(evt.run_id)}
                                    >
                                        <td className="px-space-md py-space-md text-on-surface-variant">
                                            <ChevronDown className={`h-4 w-4 transition-transform ${expandedRow === evt.run_id ? 'rotate-180' : ''}`} />
                                        </td>
                                        <td className="px-space-md py-space-md text-on-surface">
                                            <div className="flex items-center space-x-2">
                                                <Calendar className="h-4 w-4 text-on-surface-variant" />
                                                <span>{new Date(evt.timestamp).toLocaleString()}</span>
                                            </div>
                                        </td>
                                        <td className="px-space-md py-space-md font-mono text-xs text-on-surface-variant">{evt.run_id}</td>
                                        <td className="px-space-md py-space-md font-semibold text-on-surface">{evt.event_type}</td>
                                        <td className="px-space-md py-space-md text-on-surface-variant">₹{(evt.budget_paise / 100).toLocaleString()}</td>
                                        <td className="px-space-md py-space-md">
                                            {evt.status === 'SUCCESS' ? (
                                                <span className="flex items-center space-x-1 text-secondary font-medium">
                                                    <CheckCircle2 className="h-4 w-4" /> <span>Success</span>
                                                </span>
                                            ) : (
                                                <span className="flex items-center space-x-1 text-[#ba1a1a] font-medium">
                                                    <XCircle className="h-4 w-4" /> <span>Failed</span>
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                    {/* Expanded Details */}
                                    {expandedRow === evt.run_id && (
                                        <tr className="bg-surface-container-low border-b border-outline-variant/20">
                                            <td colSpan={6} className="px-14 py-6">
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                                    <div>
                                                        <h4 className="font-label-caps text-[10px] uppercase font-semibold text-on-surface-variant mb-3">Model Versions</h4>
                                                        <div className="font-mono text-xs text-on-surface bg-surface-container-lowest border border-outline-variant/30 p-3 rounded space-y-1">
                                                            <p>Optimizer: {evt.model_versions.optimizer}</p>
                                                            <p>Marginal: {evt.model_versions.marginal_impact}</p>
                                                            <p>Saturation: {evt.model_versions.saturation}</p>
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <h4 className="font-label-caps text-[10px] uppercase font-semibold text-on-surface-variant mb-3">Weights Snapshot</h4>
                                                        <div className="space-y-1 font-body-md text-sm text-on-surface">
                                                            {Object.entries(evt.weights_snapshot).map(([key, val]) => (
                                                                <div key={key} className="flex justify-between">
                                                                    <span className="capitalize text-on-surface-variant">{key.replace('_', ' ')}</span>
                                                                    <span className="font-semibold text-on-surface">{val}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <h4 className="font-label-caps text-[10px] uppercase font-semibold text-on-surface-variant mb-3">Constraints Applied</h4>
                                                        {Object.keys(evt.constraints_snapshot).length > 0 ? (
                                                            <div className="space-y-1 font-body-md text-sm text-on-surface">
                                                                {Object.entries(evt.constraints_snapshot).map(([key, val]) => (
                                                                    <div key={key} className="flex justify-between">
                                                                        <span className="capitalize text-on-surface-variant">{key.replace('_', ' ')}</span>
                                                                        <span className="font-semibold text-on-surface">{String(val)}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        ) : (
                                                            <p className="font-body-md text-sm text-on-surface-variant italic">No explicit constraints</p>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
