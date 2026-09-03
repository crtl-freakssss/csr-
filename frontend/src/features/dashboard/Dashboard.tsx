import { Link } from 'react-router-dom'

export default function Dashboard() {
    return (
        <div className="flex w-full flex-col space-y-space-xl">
            {/* Page Header */}
            <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                <div className="relative z-10 flex flex-col xl:flex-row xl:items-start justify-between gap-space-lg">
                    <div className="space-y-space-xs max-w-2xl">
                        <div className="inline-flex items-center gap-2 font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                            <span>AllocateAI / CSR Decision Platform</span>
                        </div>
                        <h1 className="font-display text-display tracking-tight text-on-surface">
                            Good morning, Admin
                        </h1>
                        <p className="font-body-lg text-body-lg text-on-surface-variant">
                            See where your next ₹1 lakh can create the greatest additional impact.
                        </p>
                    </div>
                    <div className="flex items-center gap-2 rounded bg-surface-container-low px-2 py-1 border border-outline-variant/50">
                        <span className="h-2 w-2 rounded-full bg-secondary animate-pulse"></span>
                        <span className="font-label-caps text-[10px] uppercase text-on-surface-variant">System Active • DEMO DATA</span>
                    </div>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 gap-space-md md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm border border-outline-variant/30">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Available CSR Budget
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        ₹1.00 Cr
                    </p>
                    <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                        Current allocation cycle
                    </p>
                </div>

                <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm border border-outline-variant/30">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Projects Evaluated
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        18
                    </p>
                    <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                        Across multiple sectors
                    </p>
                </div>

                <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm border border-outline-variant/30">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Highest Impact / ₹1L
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-secondary">
                        8,420
                    </p>
                    <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                        Based on latest optimization
                    </p>
                </div>

                <div className="rounded-xl bg-surface-container-lowest p-space-md shadow-sm border border-outline-variant/30">
                    <p className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant">
                        Underserved Regions
                    </p>
                    <p className="mt-2 font-tabular-stat text-tabular-stat font-semibold text-on-surface">
                        6
                    </p>
                    <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                        Low CSR saturation
                    </p>
                </div>
            </div>

            {/* Main Dashboard Layout */}
            <div className="grid grid-cols-1 gap-space-lg xl:grid-cols-3">
                {/* Left Column (Primary Opportunity & Decision Snapshot) */}
                <div className="flex flex-col gap-space-lg xl:col-span-2">
                    
                    {/* PRIMARY OPPORTUNITY */}
                    <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                        <div className="flex items-center justify-between border-b border-outline-variant/30 pb-space-sm mb-space-md">
                            <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                                Top Funding Opportunity
                            </h2>
                            <Link to="/projects/1" className="text-secondary hover:text-on-secondary-container font-label-md text-sm font-medium flex items-center gap-1 transition-colors">
                                View Project <span aria-hidden="true">&rarr;</span>
                            </Link>
                        </div>

                        <div className="flex flex-col md:flex-row gap-space-xl">
                            {/* Project Info */}
                            <div className="flex-1 space-y-space-md">
                                <div>
                                    <h3 className="font-headline-lg text-headline-lg font-bold text-on-surface">
                                        Rural Learning Initiative
                                    </h3>
                                    <p className="mt-1 font-body-md text-body-md text-on-surface-variant">
                                        Bihar · Education
                                    </p>
                                </div>

                                <div className="grid grid-cols-2 gap-space-sm">
                                    <div className="rounded bg-surface-container-low p-space-sm">
                                        <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Need Score</p>
                                        <p className="font-tabular-stat text-lg font-semibold text-on-surface">0.92</p>
                                    </div>
                                    <div className="rounded bg-surface-container-low p-space-sm">
                                        <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Saturation</p>
                                        <p className="font-tabular-stat text-lg font-semibold text-secondary">0.22</p>
                                    </div>
                                    <div className="rounded bg-surface-container-low p-space-sm">
                                        <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Evidence</p>
                                        <p className="font-tabular-stat text-lg font-semibold text-on-surface">0.88</p>
                                    </div>
                                    <div className="rounded bg-surface-container-low p-space-sm">
                                        <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Marginal Impact</p>
                                        <p className="font-tabular-stat text-lg font-semibold text-secondary">0.92</p>
                                    </div>
                                </div>
                            </div>

                            {/* Impact Callout & Reasons */}
                            <div className="flex-1 flex flex-col justify-between rounded-lg bg-surface-container-low border border-outline-variant/30 p-space-md">
                                <div>
                                    <p className="font-label-caps text-[10px] uppercase text-on-surface-variant tracking-wider">
                                        Expected Impact / ₹1L
                                    </p>
                                    <p className="mt-1 font-display text-4xl font-bold text-secondary">
                                        8,420
                                    </p>
                                    
                                    <div className="mt-space-md pt-space-sm border-t border-outline-variant/30">
                                        <p className="font-label-caps text-[10px] uppercase text-on-surface-variant tracking-wider mb-2">
                                            Decision Factors
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                            <span className="rounded bg-secondary/10 px-2 py-0.5 font-mono text-[10px] font-semibold text-secondary">HIGH_NEED</span>
                                            <span className="rounded bg-secondary/10 px-2 py-0.5 font-mono text-[10px] font-semibold text-secondary">LOW_SATURATION</span>
                                            <span className="rounded bg-on-surface/5 border border-outline-variant/50 px-2 py-0.5 font-mono text-[10px] text-on-surface-variant">STRONG_EVIDENCE</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* MARGINAL IMPACT PANEL & LATEST DECISION SNAPSHOT */}
                    <div className="grid grid-cols-1 gap-space-lg md:grid-cols-2">
                        
                        {/* Marginal Impact Panel */}
                        <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                            <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                                Marginal Impact
                            </h2>
                            <p className="mt-1 font-body-sm text-[12px] text-on-surface-variant leading-relaxed max-w-xs">
                                Where could the next ₹1 lakh create the most additional impact?
                            </p>
                            
                            <div className="mt-space-md">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-medium text-on-surface">Rural Learning Initiative</span>
                                    <span className="font-bold text-secondary">8,420</span>
                                </div>
                                <div className="h-1.5 w-full rounded-full bg-surface-container-high overflow-hidden">
                                    <div className="h-full bg-secondary w-[84%]"></div>
                                </div>
                            </div>
                            <div className="mt-space-sm">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-medium text-on-surface">Mobile Healthcare</span>
                                    <span className="font-bold text-on-surface-variant">7,850</span>
                                </div>
                                <div className="h-1.5 w-full rounded-full bg-surface-container-high overflow-hidden">
                                    <div className="h-full bg-on-surface-variant w-[78%]"></div>
                                </div>
                            </div>
                        </div>

                        {/* Latest Decision Snapshot */}
                        <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                            <div className="flex items-center justify-between mb-1">
                                <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                                    Decision Engine Result
                                </h2>
                                <span className="rounded bg-surface-container px-1.5 py-0.5 font-label-caps text-[9px] uppercase text-on-surface-variant border border-outline-variant/30">DEMO</span>
                            </div>
                            <p className="font-body-sm text-[12px] text-on-surface-variant mb-space-md">
                                Latest portfolio optimization run
                            </p>
                            
                            <div className="grid grid-cols-2 gap-y-space-md gap-x-space-sm">
                                <div>
                                    <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Budget Evaluated</p>
                                    <p className="font-tabular-stat text-md font-semibold text-on-surface">₹1.00 Cr</p>
                                </div>
                                <div>
                                    <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Projects Selected</p>
                                    <p className="font-tabular-stat text-md font-semibold text-on-surface">3</p>
                                </div>
                                <div>
                                    <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Recommended Alloc</p>
                                    <p className="font-tabular-stat text-md font-semibold text-secondary">₹95.00 L</p>
                                </div>
                                <div>
                                    <p className="font-label-caps text-[10px] uppercase text-on-surface-variant">Reserve Buffer</p>
                                    <p className="font-tabular-stat text-md font-semibold text-on-surface">₹5.00 L</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column (Portfolio Intelligence & Quick Actions) */}
                <div className="flex flex-col gap-space-lg">
                    
                    {/* PORTFOLIO INTELLIGENCE */}
                    <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface mb-space-md">
                            Portfolio Intelligence
                        </h2>
                        
                        <div className="space-y-space-sm">
                            <div className="flex items-start gap-3 rounded-lg bg-surface-container-low p-space-sm border border-outline-variant/20">
                                <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-secondary/10">
                                    <span className="block h-2 w-2 rounded-full bg-secondary"></span>
                                </div>
                                <div>
                                    <p className="font-label-md text-sm font-medium text-on-surface">High Marginal Impact</p>
                                    <p className="font-body-sm text-[11px] text-on-surface-variant mt-0.5">2 projects show exceptional incremental value in Education.</p>
                                </div>
                            </div>

                            <div className="flex items-start gap-3 rounded-lg bg-surface-container-low p-space-sm border border-outline-variant/20">
                                <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-on-surface/5">
                                    <span className="block h-2 w-2 rounded-full bg-on-surface-variant"></span>
                                </div>
                                <div>
                                    <p className="font-label-md text-sm font-medium text-on-surface">Underserved Regions</p>
                                    <p className="font-body-sm text-[11px] text-on-surface-variant mt-0.5">6 regions currently have low CSR saturation below threshold.</p>
                                </div>
                            </div>
                            
                            <div className="flex items-start gap-3 rounded-lg bg-surface-container-low p-space-sm border border-outline-variant/20">
                                <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-[#f59e0b]/10">
                                    <span className="block h-2 w-2 rounded-full bg-[#f59e0b]"></span>
                                </div>
                                <div>
                                    <p className="font-label-md text-sm font-medium text-on-surface">Review Required</p>
                                    <p className="font-body-sm text-[11px] text-on-surface-variant mt-0.5">1 project flagged for incomplete evidence documentation.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* QUICK ACTIONS */}
                    <div className="rounded-xl bg-surface-container-lowest p-space-lg shadow-sm border border-outline-variant/30">
                        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                            Quick Actions
                        </h2>
                        <p className="mt-1 font-body-sm text-[12px] text-on-surface-variant">
                            Continue your CSR decision workflow.
                        </p>

                        <div className="mt-space-lg space-y-space-md">
                            <Link
                                to="/proposals/upload"
                                className="block w-full rounded bg-secondary px-4 py-3 text-left font-label-md text-sm font-medium text-on-secondary transition hover:bg-on-secondary-container shadow-sm text-center"
                            >
                                Upload Proposal
                            </Link>
                            <Link
                                to="/optimization"
                                className="block w-full rounded border border-outline-variant px-4 py-3 text-left font-label-md text-sm font-medium text-on-surface transition hover:bg-surface-container-low text-center"
                            >
                                Run Optimization
                            </Link>
                            <Link
                                to="/allocations"
                                className="block w-full rounded border border-outline-variant px-4 py-3 text-left font-label-md text-sm font-medium text-on-surface transition hover:bg-surface-container-low text-center"
                            >
                                View Allocations
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}