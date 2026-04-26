import { useState } from "react";

export default function SearchBar({
  onSearch,
  isSearching,
  onReset,
  searchMeta,
  disabled
}) {
  const [query, setQuery] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    if (!query.trim() || disabled) {
      return;
    }
    onSearch(query.trim());
  }

  return (
    <div className="panel-backdrop rounded-3xl border border-slate-800/80 bg-panel px-4 py-4 shadow-glow">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="font-display text-lg text-white">Memory Probe</p>
          <p className="text-sm text-slate-400">
            Search the graph semantically and zoom to the strongest cluster.
          </p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="rounded-full border border-slate-700/80 px-3 py-1 text-xs uppercase tracking-[0.25em] text-slate-300 transition hover:border-slate-500 hover:text-white"
        >
          Reset
        </button>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search ideas like 'how chunking improves recall'"
          className="flex-1 rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-400/70"
        />
        <button
          type="submit"
          disabled={isSearching || disabled}
          className="rounded-2xl bg-cyan-400/90 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-300"
        >
          {isSearching ? "Scanning..." : "Search"}
        </button>
      </form>

      {searchMeta ? (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-300">
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2 py-1">
            query: {searchMeta.query}
          </span>
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1">
            matches: {searchMeta.matchCount}
          </span>
          <span className="rounded-full border border-fuchsia-500/30 bg-fuchsia-500/10 px-2 py-1">
            raw logs: {searchMeta.rawLogCount}
          </span>
        </div>
      ) : null}
    </div>
  );
}
