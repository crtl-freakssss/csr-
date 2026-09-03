import { Link } from 'react-router-dom'

const proposals = [
    {
        id: 'PROP-001',
        project: 'Rural Learning Initiative',
        organization: 'ABC Foundation',
        sector: 'EDUCATION',
        state: 'Bihar',
        budget: '₹25,00,000',
        status: 'ANALYZED',
    },
    {
        id: 'PROP-002',
        project: 'Mobile Healthcare Program',
        organization: 'Health For All',
        sector: 'HEALTHCARE',
        state: 'Rajasthan',
        budget: '₹18,00,000',
        status: 'UNDER_REVIEW',
    },
    {
        id: 'PROP-003',
        project: 'Women Skills Initiative',
        organization: 'Empower Foundation',
        sector: 'LIVELIHOOD',
        state: 'Jharkhand',
        budget: '₹15,00,000',
        status: 'ANALYZED',
    },
]

export default function Proposals() {
    return (
        <div className="flex w-full flex-col space-y-space-xl">

            {/* Header */}
            <div className="flex items-end justify-between">
                <div>
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        PROPOSAL MANAGEMENT
                    </p>
                    <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                        CSR Proposals
                    </h1>
                    <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                        Review, analyze and prioritize incoming CSR proposals.
                    </p>
                </div>

                <Link
                    to="/proposals/upload"
                    className="rounded bg-secondary px-5 py-3 font-label-md text-sm font-semibold text-on-secondary shadow-sm hover:bg-on-secondary-container transition"
                >
                    + Upload Proposal
                </Link>
            </div>

            {/* Summary cards */}
            <div className="grid gap-space-md md:grid-cols-3">
                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Total Proposals</p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        {proposals.length}
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Analyzed</p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        {proposals.filter((proposal) => proposal.status === 'ANALYZED').length}
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">Under Review</p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        {proposals.filter(
                            (proposal) => proposal.status === 'UNDER_REVIEW'
                        ).length}
                    </p>
                </div>
            </div>

            {/* Proposal table */}
            <div className="rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/30">
                <div className="border-b border-outline-variant/30 px-space-md py-space-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Submitted Proposals
                    </h2>
                </div>

                <div className="overflow-x-auto p-space-md">
                    <table className="w-full text-left font-body-md text-body-md">
                        <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            <tr>
                                <th className="rounded-l px-space-md py-2.5">Project</th>
                                <th className="px-space-md py-2.5">Organization</th>
                                <th className="px-space-md py-2.5">Sector</th>
                                <th className="px-space-md py-2.5">State</th>
                                <th className="px-space-md py-2.5">Budget</th>
                                <th className="px-space-md py-2.5">Status</th>
                                <th className="rounded-r px-space-md py-2.5"></th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-surface-container-high/40">
                            {proposals.map((proposal) => (
                                <tr
                                    key={proposal.id}
                                    className="transition-colors hover:bg-surface-container-low/50"
                                >
                                    <td className="px-space-md py-space-md">
                                        <div>
                                            <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                                                {proposal.project}
                                            </p>
                                            <p className="mt-0.5 font-body-sm text-body-sm text-on-surface-variant">
                                                {proposal.id}
                                            </p>
                                        </div>
                                    </td>

                                    <td className="px-space-md py-space-md text-on-surface-variant">
                                        {proposal.organization}
                                    </td>

                                    <td className="px-space-md py-space-md">
                                        <span className="rounded border border-outline-variant/50 px-2 py-1 font-label-caps text-[10px] uppercase text-on-surface-variant">
                                            {proposal.sector}
                                        </span>
                                    </td>

                                    <td className="px-space-md py-space-md text-on-surface-variant">
                                        {proposal.state}
                                    </td>

                                    <td className="px-space-md py-space-md font-tabular-stat font-semibold text-on-surface">
                                        {proposal.budget}
                                    </td>

                                    <td className="px-space-md py-space-md">
                                        <span
                                            className={`rounded-full px-3 py-1 font-label-caps text-[10px] font-medium ${proposal.status === 'ANALYZED'
                                                    ? 'bg-secondary/10 text-secondary'
                                                    : 'bg-[#f59e0b]/10 text-[#f59e0b]'
                                                }`}
                                        >
                                            {proposal.status.replace('_', ' ')}
                                        </span>
                                    </td>

                                    <td className="px-space-md py-space-md text-right">
                                        <Link
                                            to={`/proposals/${proposal.id}`}
                                            className="font-label-md text-sm font-medium text-secondary hover:text-on-secondary-container transition-colors"
                                        >
                                            Review →
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}