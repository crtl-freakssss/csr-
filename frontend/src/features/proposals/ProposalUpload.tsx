import { useState } from 'react'

export default function ProposalUpload() {
    const [file, setFile] = useState<File | null>(null)

    function handleFileChange(
        event: React.ChangeEvent<HTMLInputElement>
    ) {
        const selectedFile = event.target.files?.[0]
        if (selectedFile) {
            setFile(selectedFile)
        }
    }

    return (
        <div className="mx-auto max-w-4xl space-y-space-xl">

            {/* Header */}
            <div>
                <p className="font-label-caps text-label-caps uppercase tracking-wider text-secondary">
                    PROPOSALS
                </p>
                <h1 className="mt-2 font-display text-display font-semibold text-on-surface">
                    Upload CSR Proposal
                </h1>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                    Upload an NGO proposal to begin AI-assisted analysis.
                </p>
            </div>

            {/* Upload Card */}
            <div className="rounded-xl border border-outline-variant/50 bg-surface-container-lowest p-8 shadow-sm">

                <label
                    htmlFor="proposal-file"
                    className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant bg-surface-container-low px-6 py-16 text-center transition hover:border-secondary hover:bg-surface-container"
                >
                    <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary/10 text-3xl">
                        📄
                    </div>

                    <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                        {file ? file.name : 'Upload your proposal'}
                    </h2>

                    <p className="mt-2 font-body-sm text-body-sm text-on-surface-variant">
                        {file
                            ? 'Proposal selected successfully.'
                            : 'Drag and drop a PDF here, or click to browse.'}
                    </p>

                    <p className="mt-4 font-body-sm text-[11px] text-on-surface-variant">
                        Supported format: PDF
                    </p>

                    <input
                        id="proposal-file"
                        type="file"
                        accept=".pdf,application/pdf"
                        className="hidden"
                        onChange={handleFileChange}
                    />
                </label>

                {/* Selected file */}
                {file && (
                    <div className="mt-6 flex items-center justify-between rounded-lg border border-outline-variant/50 bg-surface-container-low p-4">
                        <div>
                            <p className="font-label-md text-sm font-medium text-on-surface">
                                {file.name}
                            </p>
                            <p className="mt-1 font-body-sm text-[11px] text-on-surface-variant">
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                        </div>

                        <button
                            type="button"
                            onClick={() => setFile(null)}
                            className="font-label-md text-sm text-on-surface-variant hover:text-on-surface transition-colors"
                        >
                            Remove
                        </button>
                    </div>
                )}

                {/* Upload button */}
                <button
                    type="button"
                    disabled={!file}
                    className="mt-6 w-full rounded bg-secondary px-5 py-3 font-label-md text-sm font-semibold text-on-secondary shadow-sm transition hover:bg-on-secondary-container disabled:cursor-not-allowed disabled:opacity-40"
                >
                    Upload & Analyze Proposal
                </button>

            </div>

            {/* Process information */}
            <div className="grid gap-space-md md:grid-cols-3">

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-md text-sm font-semibold text-on-surface">
                        01 · Extract
                    </p>
                    <p className="mt-2 font-body-sm text-body-sm text-on-surface-variant">
                        Extract structured information from the proposal.
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-md text-sm font-semibold text-on-surface">
                        02 · Analyze
                    </p>
                    <p className="mt-2 font-body-sm text-body-sm text-on-surface-variant">
                        Generate proposal evidence and Impact DNA.
                    </p>
                </div>

                <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-space-md shadow-sm">
                    <p className="font-label-md text-sm font-semibold text-on-surface">
                        03 · Decide
                    </p>
                    <p className="mt-2 font-body-sm text-body-sm text-on-surface-variant">
                        Feed validated data into the deterministic decision engine.
                    </p>
                </div>

            </div>

        </div>
    )
}