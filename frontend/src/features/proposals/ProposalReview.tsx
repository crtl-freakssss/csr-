import { Link, useParams } from 'react-router-dom'

export default function ProposalReview() {
    const { id } = useParams()

    return (
        <div className="flex w-full flex-col space-y-space-xl">

            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        PROPOSAL REVIEW
                    </p>
                    <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                        Rural Learning Initiative
                    </h1>
                    <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                        Proposal ID: {id}
                    </p>
                </div>

                <Link
                    to="/proposals"
                    className="rounded border border-outline-variant px-4 py-2 font-label-md text-sm font-medium text-on-surface hover:bg-surface-container-low transition"
                >
                    ← Back to Proposals
                </Link>
            </div>

            {/* Proposal overview */}
            <div className="grid gap-space-md md:grid-cols-4">

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-[10px] uppercase tracking-wider text-on-surface-variant">
                        Organization
                    </p>
                    <p className="mt-2 font-label-md text-sm font-semibold text-on-surface">
                        ABC Foundation
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-[10px] uppercase tracking-wider text-on-surface-variant">
                        Sector
                    </p>
                    <p className="mt-2 font-label-md text-sm font-semibold text-on-surface">
                        Education
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-[10px] uppercase tracking-wider text-on-surface-variant">
                        State
                    </p>
                    <p className="mt-2 font-label-md text-sm font-semibold text-on-surface">
                        Bihar
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-[10px] uppercase tracking-wider text-on-surface-variant">
                        Requested Budget
                    </p>
                    <p className="mt-2 font-tabular-stat font-semibold text-on-surface">
                        ₹25,00,000
                    </p>
                </div>

            </div>

            {/* Analysis */}
            <div className="grid gap-space-lg lg:grid-cols-2">

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Proposal Summary
                    </h2>
                    <p className="mt-4 font-body-md text-body-md leading-7 text-on-surface-variant">
                        The project proposes improving access to foundational education
                        for students in underserved rural communities through learning
                        centers, trained educators and locally delivered educational
                        support.
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        AI Analysis Status
                    </h2>
                    <div className="mt-5 flex items-center gap-3">
                        <span className="h-3 w-3 rounded-full bg-secondary" />
                        <span className="font-label-md text-sm font-semibold text-secondary">
                            Analysis Complete
                        </span>
                    </div>
                    <p className="mt-4 font-body-md text-body-md leading-6 text-on-surface-variant">
                        Proposal information has been extracted and is ready for
                        deterministic impact and allocation analysis.
                    </p>
                </div>

            </div>

            {/* Impact signals */}
            <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">

                <div className="flex items-center justify-between border-b border-outline-variant/30 pb-space-sm mb-space-md">
                    <div>
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                            Impact Signals
                        </h2>
                        <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">
                            Initial signals extracted from the proposal.
                        </p>
                    </div>

                    <Link
                        to="/projects/1/impact-dna"
                        className="rounded border border-outline-variant px-4 py-2 font-label-md text-sm font-semibold text-on-surface hover:bg-surface-container-low transition"
                    >
                        View Impact DNA →
                    </Link>
                </div>

                <div className="grid gap-space-sm md:grid-cols-3">

                    <div className="rounded-lg bg-surface-container-low p-space-md">
                        <p className="font-label-caps text-[10px] uppercase tracking-wider text-on-surface-variant">
                            Need Level
                        </p>
                        <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                            High
                        </p>
                    </div>

                    <div className="rounded-lg bg-surface-container-low p-space-md">
                        <p className="font-label-caps text-[10px] uppercase tracking-wider text-on-surface-variant">
                            Evidence
                        </p>
                        <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                            Strong
                        </p>
                    </div>

                    <div className="rounded-lg bg-surface-container-low p-space-md">
                        <p className="font-label-caps text-[10px] uppercase tracking-wider text-on-surface-variant">
                            Scalability
                        </p>
                        <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                            High
                        </p>
                    </div>

                </div>
            </div>

            {/* Reason codes */}
            <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-lg shadow-sm">
                <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface mb-space-md">
                    Decision Signals
                </h2>
                <div className="flex flex-wrap gap-3">
                    <span className="rounded bg-secondary/10 px-4 py-2 font-mono text-xs font-semibold text-secondary">
                        HIGH_NEED
                    </span>
                    <span className="rounded bg-secondary/10 px-4 py-2 font-mono text-xs font-semibold text-secondary">
                        LOW_SATURATION
                    </span>
                    <span className="rounded bg-secondary/10 px-4 py-2 font-mono text-xs font-semibold text-secondary">
                        STRONG_EVIDENCE
                    </span>
                    <span className="rounded bg-secondary/10 px-4 py-2 font-mono text-xs font-semibold text-secondary">
                        HIGH_SCALABILITY
                    </span>
                </div>
            </div>

        </div>
    )
}