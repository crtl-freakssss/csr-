import { Link } from 'react-router-dom'

const regions = [
    {
        state: 'Bihar',
        sector: 'Education',
        need: 0.91,
        saturation: 0.22,
        opportunity: 0.89,
    },
    {
        state: 'Jharkhand',
        sector: 'Livelihood',
        need: 0.87,
        saturation: 0.31,
        opportunity: 0.84,
    },
    {
        state: 'Rajasthan',
        sector: 'Healthcare',
        need: 0.82,
        saturation: 0.44,
        opportunity: 0.76,
    },
    {
        state: 'Odisha',
        sector: 'Education',
        need: 0.79,
        saturation: 0.38,
        opportunity: 0.81,
    },
]

export default function Saturation() {
    return (
        <div className="flex w-full flex-col space-y-space-xl">

            {/* Header */}
            <div className="flex items-end justify-between">
                <div>
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        GEOGRAPHIC INTELLIGENCE
                    </p>
                    <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                        CSR Saturation
                    </h1>
                    <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                        Identify areas where CSR funding is concentrated or underserved.
                    </p>
                </div>

                <Link
                    to="/optimization"
                    className="rounded border border-outline-variant bg-surface-container-lowest px-5 py-3 font-label-md text-sm font-semibold text-on-surface shadow-sm hover:bg-surface-container-low transition"
                >
                    Continue to Optimizer →
                </Link>
            </div>

            {/* Key insight */}
            <div className="rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-6 shadow-sm">
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    Saturation Insight
                </p>
                <h2 className="mt-2 font-headline-lg text-headline-lg font-semibold text-on-surface">
                    Bihar shows a high-need, low-saturation opportunity
                </h2>
                <p className="mt-2 max-w-3xl font-body-md text-body-md text-on-surface-variant">
                    The saturation view helps identify where additional CSR funding
                    could have greater incremental impact because existing funding
                    coverage is relatively low.
                </p>
            </div>

            {/* Overview */}
            <div className="grid gap-space-md md:grid-cols-3">
                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Regions Analyzed
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        18
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Underserved Regions
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        6
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Highest Opportunity
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        Bihar
                    </p>
                </div>
            </div>

            {/* Region table */}
            <div className="rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/30">
                <div className="border-b border-outline-variant/30 px-space-md py-space-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Regional Saturation Analysis
                    </h2>
                    <p className="mt-1 font-body-sm text-body-sm text-on-surface-variant">
                        Lower saturation combined with higher need indicates stronger
                        funding opportunity.
                    </p>
                </div>

                <div className="overflow-x-auto p-space-md">
                    <table className="w-full text-left font-body-md text-body-md">
                        <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            <tr>
                                <th className="rounded-l px-space-md py-2.5">Region</th>
                                <th className="px-space-md py-2.5">Sector</th>
                                <th className="px-space-md py-2.5">Need</th>
                                <th className="px-space-md py-2.5">CSR Saturation</th>
                                <th className="rounded-r px-space-md py-2.5">Opportunity</th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-surface-container-high/40">
                            {regions.map((region) => (
                                <tr
                                    key={`${region.state}-${region.sector}`}
                                    className="transition-colors hover:bg-surface-container-low/50"
                                >
                                    <td className="px-space-md py-space-md font-semibold text-on-surface">
                                        {region.state}
                                    </td>

                                    <td className="px-space-md py-space-md text-on-surface-variant">
                                        {region.sector}
                                    </td>

                                    <td className="px-space-md py-space-md">
                                        <div className="flex items-center gap-3">
                                            <div className="h-2 w-24 rounded-full bg-surface-container-high overflow-hidden">
                                                <div
                                                    className="h-2 rounded-full bg-secondary"
                                                    style={{ width: `${region.need * 100}%` }}
                                                />
                                            </div>
                                            <span className="font-tabular-stat text-sm text-on-surface">
                                                {Math.round(region.need * 100)}%
                                            </span>
                                        </div>
                                    </td>

                                    <td className="px-space-md py-space-md">
                                        <div className="flex items-center gap-3">
                                            <div className="h-2 w-24 rounded-full bg-surface-container-high overflow-hidden">
                                                <div
                                                    className="h-2 rounded-full bg-on-surface-variant"
                                                    style={{ width: `${region.saturation * 100}%` }}
                                                />
                                            </div>
                                            <span className="font-tabular-stat text-sm text-on-surface-variant">
                                                {Math.round(region.saturation * 100)}%
                                            </span>
                                        </div>
                                    </td>

                                    <td className="px-space-md py-space-md">
                                        <span className="rounded-full bg-secondary/10 px-3 py-1 font-label-md text-label-md font-semibold text-secondary">
                                            {Math.round(region.opportunity * 100)}%
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Explanation */}
            <div className="rounded-xl bg-surface-container-lowest p-6 shadow-sm border border-outline-variant/30">
                <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                    How to read this view
                </h2>

                <div className="mt-space-md grid gap-space-sm md:grid-cols-3">
                    <div className="rounded-lg bg-surface-container-low p-space-md">
                        <p className="font-label-md text-label-md font-semibold text-on-surface">
                            High Need
                        </p>
                        <p className="mt-2 font-body-sm text-body-sm text-on-surface-variant">
                            Indicates stronger unmet social or development needs.
                        </p>
                    </div>

                    <div className="rounded-lg bg-surface-container-low p-space-md">
                        <p className="font-label-md text-label-md font-semibold text-on-surface">
                            Low Saturation
                        </p>
                        <p className="mt-2 font-body-sm text-body-sm text-on-surface-variant">
                            Indicates relatively lower existing CSR activity.
                        </p>
                    </div>

                    <div className="rounded-lg bg-surface-container-low p-space-md">
                        <p className="font-label-md text-label-md font-semibold text-on-surface">
                            Opportunity
                        </p>
                        <p className="mt-2 font-body-sm text-body-sm text-on-surface-variant">
                            Combines need and saturation to highlight potential funding
                            opportunities.
                        </p>
                    </div>
                </div>
            </div>

        </div>
    )
}