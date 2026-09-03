import { useState, useEffect } from 'react';
import { Loader2, Settings2, AlertCircle, CheckCircle2, Save, RotateCcw } from 'lucide-react';
import type { ApiError } from '../../types';


type State = 'LOADING' | 'SUCCESS' | 'ERROR' | 'EMPTY' | 'SAVING';

export default function Settings() {
    const [state, setState] = useState<State>('LOADING');
    const [error, setError] = useState<ApiError | null>(null);
    const [saveMessage, setSaveMessage] = useState('');

    const [weights, setWeights] = useState({
        need: 30,
        marginalImpact: 30,
        saturation: 20,
        costEfficiency: 10,
        evidence: 5,
        risk: 5
    });

    useEffect(() => {
        // Simulate loading settings from backend
        setTimeout(() => {
            setState('SUCCESS');
        }, 800);
    }, []);

    const handleSave = () => {
        setState('SAVING');
        setError(null);
        setSaveMessage('');

        // Simulate API call to save settings
        setTimeout(() => {
            setState('SUCCESS');
            setSaveMessage('Configuration saved successfully to Decision Engine.');
            setTimeout(() => setSaveMessage(''), 3000);
        }, 1000);
    };

    const handleReset = () => {
        setWeights({
            need: 30,
            marginalImpact: 30,
            saturation: 20,
            costEfficiency: 10,
            evidence: 5,
            risk: 5
        });
    };

    const handleWeightChange = (key: keyof typeof weights, value: string) => {
        setWeights(prev => ({ ...prev, [key]: Number(value) }));
    };

    const totalWeight = Object.values(weights).reduce((acc, curr) => acc + curr, 0);

    return (
        <div className="mx-auto max-w-4xl space-y-8">
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    CONFIGURATION
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    Decision Engine Configuration
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    Tune the weights for the backend optimizer. These controls do not calculate allocations directly.
                </p>
                <div className="mt-4 inline-flex items-center space-x-2 rounded-full bg-secondary/10 px-3 py-1 text-sm text-secondary">
                    <Settings2 className="h-4 w-4" />
                    <span>Inputs act as configuration for the backend system.</span>
                </div>
            </div>

            {state === 'LOADING' ? (
                <div className="flex h-64 flex-col items-center justify-center space-y-4 rounded-xl border border-outline-variant/50 bg-surface-container-lowest shadow-sm">
                    <Loader2 className="h-8 w-8 animate-spin text-on-surface-variant" />
                    <p className="font-body-sm text-body-sm text-on-surface-variant">Loading current configuration...</p>
                </div>
            ) : (
                <div className="space-y-6">
                    {state === 'ERROR' && error && (
                        <div className="rounded-md bg-red-500/10 border border-red-500/20 p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <AlertCircle className="h-5 w-5 text-red-500" />
                                </div>
                                <div className="ml-3">
                                    <h3 className="text-sm font-medium text-red-700">Error saving configuration</h3>
                                    <div className="mt-2 text-sm text-red-600">
                                        <p>{error.error.message}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {saveMessage && (
                        <div className="rounded-md bg-green-500/10 border border-green-500/20 p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                                </div>
                                <div className="ml-3 text-sm font-medium text-green-700">
                                    {saveMessage}
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-6 lg:p-8 shadow-sm">
                        <div className="mb-6 flex items-center justify-between">
                            <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Impact Weights</h2>
                            <div className={`text-sm font-medium ${totalWeight === 100 ? 'text-secondary' : 'text-[#f59e0b]'}`}>
                                Total: {totalWeight}% {totalWeight !== 100 && '(Should equal 100%)'}
                            </div>
                        </div>

                        <div className="space-y-6">
                            {Object.entries(weights).map(([key, value]) => (
                                <div key={key}>
                                    <div className="flex justify-between mb-2">
                                        <label className="font-label-md text-label-md font-medium text-on-surface capitalize">
                                            {key.replace(/([A-Z])/g, ' $1').trim()}
                                        </label>
                                        <span className="font-label-md text-label-md text-on-surface-variant">{value}%</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0"
                                        max="100"
                                        value={value}
                                        onChange={(e) => handleWeightChange(key as keyof typeof weights, e.target.value)}
                                        className="w-full h-2 bg-surface-container-high rounded-lg appearance-none cursor-pointer accent-secondary"
                                    />
                                </div>
                            ))}
                        </div>
                        
                        <div className="mt-10 flex items-center space-x-4 border-t border-outline-variant/30 pt-6">
                            <button
                                onClick={handleSave}
                                disabled={state === 'SAVING' || totalWeight !== 100}
                                className="flex items-center space-x-2 rounded bg-secondary px-6 py-2 font-label-md text-sm font-semibold text-on-secondary transition hover:bg-on-secondary-container disabled:opacity-50 shadow-sm"
                            >
                                {state === 'SAVING' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                                <span>Save Configuration</span>
                            </button>
                            <button
                                onClick={handleReset}
                                disabled={state === 'SAVING'}
                                className="flex items-center space-x-2 rounded border border-outline-variant px-6 py-2 font-label-md text-sm font-medium text-on-surface transition hover:bg-surface-container-low disabled:opacity-50"
                            >
                                <RotateCcw className="h-4 w-4 text-on-surface-variant" />
                                <span>Reset Defaults</span>
                            </button>
                        </div>
                    </div>

                    {/* Meta information */}
                    <div className="rounded-xl border border-outline-variant/30 bg-surface-container-low p-6">
                        <h2 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-4">System Information</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <p className="font-label-caps text-[10px] uppercase text-on-surface-variant mb-1">Optimizer Version</p>
                                <p className="font-mono text-sm font-medium text-on-surface">optimizer-v1</p>
                            </div>
                            <div>
                                <p className="font-label-caps text-[10px] uppercase text-on-surface-variant mb-1">Model Version</p>
                                <p className="font-mono text-sm font-medium text-on-surface">marginal-v1</p>
                            </div>
                            <div>
                                <p className="font-label-caps text-[10px] uppercase text-on-surface-variant mb-1">Schema Version</p>
                                <p className="font-mono text-sm font-medium text-on-surface">v1.0</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
