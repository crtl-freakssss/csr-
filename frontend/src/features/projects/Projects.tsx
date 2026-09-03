const projects = [
    {
        rank: 1,
        project: 'Rural Learning Initiative',
        organization: 'ABC Foundation',
        sector: 'Education',
        state: 'Bihar',
        impact: '8,420',
        marginal: '0.92',
        score: '0.91',
    },
    {
        rank: 2,
        project: 'Mobile Healthcare Program',
        organization: 'Health For All',
        sector: 'Healthcare',
        state: 'Rajasthan',
        impact: '7,850',
        marginal: '0.87',
        score: '0.86',
    },
    {
        rank: 3,
        project: 'Women Skills Initiative',
        organization: 'Empower Foundation',
        sector: 'Livelihood',
        state: 'Jharkhand',
        impact: '7,210',
        marginal: '0.81',
        score: '0.82',
    },
]

export default function Projects() {
    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Header Hero */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg lg:p-space-xl shadow-sm">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 rounded-full bg-secondary-fixed/50 px-space-sm py-1 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <span>DECISION ENGINE</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Project Ranking
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            Compare projects by need, marginal impact and decision score.
                        </p>
                    </div>
                </div>
            </div>

            {/* Key insight */}
            <div className="rounded-xl border border-outline-variant/50 bg-surface-container-low p-space-lg">
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                    Allocation Insight
                </p>
                <h2 className="mt-2 font-headline-md text-headline-md font-semibold text-on-surface">
                    Where will the next ₹1 lakh create the most impact?
                </h2>
                <p className="mt-2 max-w-3xl font-body-md text-body-md text-on-surface-variant">
                    The ranking combines project impact signals with marginal impact
                    to identify opportunities where additional CSR funding can create
                    the greatest incremental value.
                </p>
            </div>

            {/* Ranking table */}
            <div className="rounded-xl bg-surface-container-lowest shadow-sm">
                <div className="border-b border-surface-container-high px-space-md py-space-sm">
                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        Ranked Projects
                    </h2>
                </div>

                <div className="overflow-x-auto p-space-md">
                    <table className="w-full text-left font-body-md text-body-md">
                        <thead className="bg-surface-container-low font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                            <tr>
                                <th className="rounded-l px-space-md py-2.5">Rank</th>
                                <th className="px-space-md py-2.5">Project</th>
                                <th className="px-space-md py-2.5">Sector</th>
                                <th className="px-space-md py-2.5">State</th>
                                <th className="px-space-md py-2.5">Impact / ₹1L</th>
                                <th className="px-space-md py-2.5">Marginal Impact</th>
                                <th className="rounded-r px-space-md py-2.5">Score</th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-surface-container-high/40">
                            {projects.map((project) => (
                                <tr
                                    key={project.rank}
                                    className="transition-colors hover:bg-surface-container-low/50"
                                >
                                    <td className="px-space-md py-space-md align-top">
                                        <span className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                                            #{project.rank}
                                        </span>
                                    </td>

                                    <td className="px-space-md py-space-md align-top">
                                        <p className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                                            {project.project}
                                        </p>
                                        <p className="mt-0.5 font-body-sm text-body-sm text-on-surface-variant">
                                            {project.organization}
                                        </p>
                                    </td>

                                    <td className="px-space-md py-space-md align-top font-label-md text-label-md text-on-surface">
                                        {project.sector}
                                    </td>

                                    <td className="px-space-md py-space-md align-top font-body-sm text-body-sm text-on-surface-variant">
                                        {project.state}
                                    </td>

                                    <td className="px-space-md py-space-md align-top font-tabular-stat text-headline-sm font-semibold text-on-surface">
                                        {project.impact}
                                    </td>

                                    <td className="px-space-md py-space-md align-top">
                                        <span className="rounded-full bg-secondary-fixed/50 px-3 py-1 font-label-caps text-label-caps font-semibold text-secondary">
                                            {project.marginal}
                                        </span>
                                    </td>

                                    <td className="px-space-md py-space-md align-top font-tabular-stat text-headline-sm font-semibold text-on-surface">
                                        {project.score}
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