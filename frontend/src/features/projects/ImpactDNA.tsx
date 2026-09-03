import { Link, useParams } from 'react-router-dom'

const impactSignals = [
    { label: 'Need', value: 0.92 },
    { label: 'Evidence', value: 0.88 },
    { label: 'Scalability', value: 0.84 },
    { label: 'Cost Efficiency', value: 0.91 },
    { label: 'Implementation Risk', value: 0.28 },
    { label: 'Saturation', value: 0.22 },
]

export default function ImpactDNA() {
    const { id } = useParams()

    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-secondary-fixed/50 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                        <span>PROJECT INTELLIGENCE</span>
                    </div>
                    <h1 className="mt-2 font-display text-display tracking-tight text-on-surface">
                        Impact DNA
                    </h1>
                    <p className="mt-2 font-body-lg text-body-lg text-on-surface-variant">
                        Rural Learning Initiative · Project ID: {id}
                    </p>
                </div>
                <Link
                    to="/projects"
                    className="rounded border border-outline-variant px-4 py-2 font-label-md text-label-md font-medium text-on-surface transition hover:bg-surface-container-low"
                >
                    ← Back to Projects
                </Link>
            </div>

            {/* Main insight */}
            <div className="rounded-xl border border-outline-variant/50 bg-surface-container-low p-space-lg shadow-sm">
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    Impact Profile
                </p>

                <div className="mt-space-md flex flex-col justify-between gap-space-lg md:flex-row md:items-end">
                    <div>
                        <h2 className="font-headline-lg text-headline-lg font-semibold text-on-surface">
                            High potential, low saturation
                        </h2>
                        <p className="mt-2 max-w-2xl font-body-md text-body-md text-on-surface-variant">
                            This project combines strong demonstrated need, credible
                            evidence and high cost efficiency with relatively low
                            saturation in the target region.
                        </p>
                    </div>

                    <div className="text-left md:text-right">
                        <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            Impact / ₹1L
                        </p>
                        <p className="mt-1 font-headline-lg text-headline-lg font-semibold text-secondary">
                            8,420
                        </p>
                    </div>
                </div>
            </div>

            {/* Signal cards */}
            <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm">
                <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                    Impact Signals
                </h2>

                <div className="mt-space-md grid gap-space-md md:grid-cols-2 lg:grid-cols-3">
                    {impactSignals.map((signal) => (
                        <div
                            key={signal.label}
                            className="rounded-lg border border-outline-variant/30 bg-surface-container-low p-space-md"
                        >
                            <div className="flex items-center justify-between">
                                <p className="font-body-sm text-body-sm text-on-surface-variant">
                                    {signal.label}
                                </p>
                                <p className="font-tabular-stat text-headline-sm font-semibold text-on-surface">
                                    {Math.round(signal.value * 100)}%
                                </p>
                            </div>

                            <div className="mt-space-sm h-1.5 overflow-hidden rounded-full bg-surface-container-highest">
                                <div
                                    className="h-full rounded-full bg-secondary"
                                    style={{ width: `${signal.value * 100}%` }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Impact explanation */}
            <div className="grid gap-space-lg lg:grid-cols-2">
                <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Why this project scores well
                    </h2>

                    <div className="mt-space-md space-y-space-sm">
                        <div className="rounded-lg bg-surface-container-low p-space-md">
                            <p className="font-label-md text-label-md font-semibold text-on-surface">
                                HIGH_NEED
                            </p>
                            <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">
                                Target communities show significant unmet educational need.
                            </p>
                        </div>

                        <div className="rounded-lg bg-surface-container-low p-space-md">
                            <p className="font-label-md text-label-md font-semibold text-on-surface">
                                LOW_SATURATION
                            </p>
                            <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">
                                Existing CSR activity in the target geography remains
                                relatively limited.
                            </p>
                        </div>

                        <div className="rounded-lg bg-surface-container-low p-space-md">
                            <p className="font-label-md text-label-md font-semibold text-on-surface">
                                STRONG_EVIDENCE
                            </p>
                            <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">
                                The proposal provides supporting evidence for its expected
                                outcomes.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Marginal Impact
                    </h2>

                    <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                        Estimated additional impact from allocating more CSR funding
                        to this project.
                    </p>

                    <div className="mt-space-xl">
                        <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            Marginal Impact Score
                        </p>
                        <p className="mt-2 font-display text-display font-semibold text-secondary">
                            0.92
                        </p>
                        <p className="mt-3 font-label-md text-label-md font-semibold text-on-surface">
                            HIGH_MARGINAL_IMPACT
                        </p>
                    </div>

                    <div className="mt-space-xl rounded-lg border border-outline-variant/30 bg-surface-container-low p-space-md">
                        <p className="font-label-md text-label-md font-semibold text-on-surface">
                            Decision implication
                        </p>
                        <p className="mt-2 font-body-sm text-body-sm text-on-surface-variant">
                            Additional funding is expected to generate meaningful
                            incremental impact compared with more saturated alternatives.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}