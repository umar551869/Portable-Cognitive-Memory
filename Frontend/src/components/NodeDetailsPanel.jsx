const TYPE_COLORS = {
  concept:  { bg: "bg-cyan-500/10",   border: "border-cyan-500/30",   text: "text-cyan-300",   dot: "#00f2ff" },
  process:  { bg: "bg-emerald-500/10", border: "border-emerald-500/30", text: "text-emerald-300", dot: "#00ff8c" },
  decision: { bg: "bg-orange-500/10", border: "border-orange-500/30", text: "text-orange-300",  dot: "#ffb86c" },
  artifact: { bg: "bg-purple-500/10", border: "border-purple-500/30", text: "text-purple-300",  dot: "#bd93f9" },
  unknown:  { bg: "bg-slate-800/40",  border: "border-slate-700/40",  text: "text-slate-400",   dot: "#7c8cf8" }
};

function getTypeStyle(type) {
  return TYPE_COLORS[type?.toLowerCase()] || TYPE_COLORS.unknown;
}

function Section({ label, color = "text-slate-400", children }) {
  return (
    <section>
      <p className={`mb-2 text-[10px] font-bold uppercase tracking-[0.3em] ${color}`}>{label}</p>
      {children}
    </section>
  );
}

export default function NodeDetailsPanel({ node, connectedNodes, relatedLinks, rawLogs }) {
  const style = node ? getTypeStyle(node.type) : null;

  return (
    <aside className="panel-backdrop flex flex-col rounded-[2rem] border border-slate-800/80 bg-panel shadow-greenGlow">
      {/* Header */}
      <div className="border-b border-slate-800/80 px-5 py-4">
        <p className="font-display text-base text-white">Memory Focus</p>
        <p className="mt-0.5 text-xs text-slate-500">
          Click any node to inspect its cognitive context.
        </p>
      </div>

      {/* Scrollable body */}
      <div className="scroll-thin flex-1 overflow-y-auto px-5 py-5">
        {node ? (
          <div className="space-y-5">
            {/* Node identity */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
                  style={{ background: style.dot, boxShadow: `0 0 6px ${style.dot}` }}
                />
                <p className={`text-[10px] font-bold uppercase tracking-[0.3em] ${style.text}`}>
                  {node.type || "unknown"}
                </p>
              </div>
              <h2 className="font-display text-2xl leading-tight text-white">{node.name}</h2>

              {/* Badges */}
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <span className={`rounded-full border ${style.border} ${style.bg} ${style.text} px-3 py-1`}>
                  {node.type}
                </span>
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-emerald-300">
                  weight {node.weight}
                </span>
                <span className="rounded-full border border-fuchsia-500/30 bg-fuchsia-500/10 px-3 py-1 text-fuchsia-300">
                  {connectedNodes.length} neighbors
                </span>
              </div>
            </div>

            {/* Description — the key panel */}
            <Section label="Description" color="text-cyan-400">
              <div className="rounded-2xl border border-cyan-500/15 bg-cyan-500/5 px-4 py-4">
                <p className="text-sm leading-7 text-slate-200">
                  {node.description && node.description.trim()
                    ? node.description
                    : "No description has been extracted for this node yet. Ingest more context to populate this field."}
                </p>
              </div>
            </Section>

            {/* Canonical name / aliases */}
            {(node.canonicalName || node.aliases?.length > 0) && (
              <Section label="Identity" color="text-slate-400">
                <div className="space-y-2">
                  {node.canonicalName && node.canonicalName !== node.name && (
                    <div className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
                      <p className="text-[10px] uppercase tracking-widest text-slate-500">Canonical</p>
                      <p className="mt-0.5 text-sm text-slate-200">{node.canonicalName}</p>
                    </div>
                  )}
                  {node.aliases?.length > 0 && (
                    <div className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
                      <p className="text-[10px] uppercase tracking-widest text-slate-500">Aliases</p>
                      <p className="mt-0.5 text-sm text-slate-200">{node.aliases.join(", ")}</p>
                    </div>
                  )}
                </div>
              </Section>
            )}

            {/* Relationships */}
            <Section label="Relationships" color="text-orange-400">
              <div className="space-y-2">
                {relatedLinks.length ? (
                  relatedLinks.map((link, i) => (
                    <div
                      key={`${link.source}-${link.target}-${i}`}
                      className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-3"
                    >
                      <p className="text-xs font-semibold uppercase tracking-wider text-orange-300">
                        {link.relation}
                      </p>
                      {link.evidence && (
                        <p className="mt-1.5 text-xs leading-5 text-slate-400">{link.evidence}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-3 text-xs text-slate-500">
                    No relationships found for this node.
                  </p>
                )}
              </div>
            </Section>

            {/* Related concepts */}
            <Section label="Connected Concepts" color="text-emerald-400">
              <div className="space-y-2">
                {connectedNodes.length ? (
                  connectedNodes.map((rel) => {
                    const relStyle = getTypeStyle(rel.type);
                    return (
                      <div
                        key={rel.id}
                        className="flex items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2.5"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span
                            className="h-2 w-2 flex-shrink-0 rounded-full"
                            style={{ background: relStyle.dot }}
                          />
                          <p className="truncate text-sm text-white">{rel.name}</p>
                        </div>
                        <span className={`flex-shrink-0 text-[10px] uppercase tracking-wider ${relStyle.text}`}>
                          {rel.type}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <p className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-3 text-xs text-slate-500">
                    No connected concepts in current view.
                  </p>
                )}
              </div>
            </Section>

            {/* Supporting memory logs */}
            {rawLogs?.length > 0 && (
              <Section label="Supporting Memory" color="text-fuchsia-400">
                <div className="space-y-2">
                  {rawLogs.map((log) => (
                    <div
                      key={log.id}
                      className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-3"
                    >
                      <p className="text-[10px] uppercase tracking-wider text-slate-500">{log.source_path}</p>
                      <p className="mt-2 text-xs leading-5 text-slate-300">{log.excerpt}</p>
                    </div>
                  ))}
                </div>
              </Section>
            )}
          </div>
        ) : (
          /* Empty state */
          <div className="flex h-full min-h-[16rem] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-950/30 px-6 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-500/20 bg-cyan-500/5">
              <div className="h-3 w-3 animate-pulse rounded-full bg-cyan-400" />
            </div>
            <p className="font-display text-lg text-white">No Node Selected</p>
            <p className="mt-2 max-w-[220px] text-xs leading-5 text-slate-500">
              Click any glowing node in the neural graph to inspect its full cognitive context.
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
