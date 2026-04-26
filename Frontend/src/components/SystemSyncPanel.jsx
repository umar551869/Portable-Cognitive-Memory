import { useState, useEffect } from "react";
import { scanSystem, watchSystem, ingestDirectory } from "../api";

export default function SystemSyncPanel({ token, onIngestSuccess }) {
  const [discoveredPaths, setDiscoveredPaths] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [isWatching, setIsWatching] = useState(false);
  const [ingestProgress, setIngestProgress] = useState(null); // { current, total, label }

  async function handleScan() {
    setIsScanning(true);
    try {
      const { paths } = await scanSystem(token);
      setDiscoveredPaths(paths);
    } catch (error) {
      console.error("Scan failed:", error);
    } finally {
      setIsScanning(false);
    }
  }

  async function handleInitialize() {
    if (!discoveredPaths.length) return;
    
    setIngestProgress({ current: 0, total: discoveredPaths.length, label: "Initializing Neural Ingest..." });
    
    for (let i = 0; i < discoveredPaths.length; i++) {
      const path = discoveredPaths[i];
      setIngestProgress({ 
        current: i + 1, 
        total: discoveredPaths.length, 
        label: `Ingesting: ${path.split(/[\\/]/).pop()}` 
      });
      try {
        await ingestDirectory(path, "system_sync", token);
      } catch (error) {
        console.error(`Failed to ingest ${path}:`, error);
      }
    }
    
    setIngestProgress(null);
    if (onIngestSuccess) onIngestSuccess();
  }

  async function handleWatch() {
    setIsWatching(true);
    try {
      await watchSystem(token);
    } catch (error) {
      console.error("Watch failed:", error);
    } finally {
      // Stay "watching" visually
    }
  }

  return (
    <div className="panel-backdrop rounded-[2rem] border border-slate-800/80 bg-slate-950/40 p-6 shadow-glow transition-all">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl text-white">System Synchronizer</h2>
          <p className="text-xs text-slate-400">Discover and monitor your local cognitive history.</p>
        </div>
        <div className={`h-2 w-2 rounded-full ${isWatching ? 'bg-cyan-500 animate-pulse shadow-[0_0_10px_rgba(6,182,212,0.5)]' : 'bg-slate-700'}`} />
      </div>

      {!discoveredPaths.length ? (
        <button
          onClick={handleScan}
          disabled={isScanning}
          className="group relative w-full overflow-hidden rounded-2xl bg-slate-900/50 p-8 border border-slate-800 transition-all hover:border-cyan-500/50 hover:bg-cyan-500/5"
        >
          <div className="relative z-10 flex flex-col items-center">
            <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 ${isScanning ? 'animate-spin' : ''}`}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <span className="font-bold text-slate-200">{isScanning ? "Scanning Neural Pathways..." : "Scan System for History"}</span>
            <span className="mt-2 text-xs text-slate-500">Finds projects, shell history, and local documents.</span>
          </div>
        </button>
      ) : (
        <div className="space-y-4">
          <div className="max-h-48 overflow-y-auto pr-2 scroll-thin">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Discovered Nodes</div>
            {discoveredPaths.map((path, idx) => (
              <div key={idx} className="mb-2 flex items-center gap-3 rounded-xl bg-slate-900/30 p-3 border border-slate-800/50">
                <div className="h-1.5 w-1.5 rounded-full bg-cyan-500/50" />
                <span className="truncate text-xs text-slate-400 font-mono">{path}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleInitialize}
              disabled={!!ingestProgress}
              className="flex-1 rounded-xl bg-cyan-500 px-4 py-3 text-xs font-bold uppercase tracking-widest text-slate-950 transition-all hover:bg-cyan-400 disabled:opacity-50"
            >
              Initialize Memory
            </button>
            <button
              onClick={handleWatch}
              disabled={isWatching}
              className={`rounded-xl border px-4 py-3 text-xs font-bold uppercase tracking-widest transition-all ${
                isWatching 
                ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-400' 
                : 'border-slate-800 bg-slate-900/50 text-slate-400 hover:border-cyan-500/50 hover:text-cyan-400'
              }`}
            >
              {isWatching ? "Monitoring Active" : "Engage Watcher"}
            </button>
          </div>
          
          <button 
            onClick={() => setDiscoveredPaths([])}
            className="w-full py-2 text-[10px] uppercase tracking-[0.2em] text-slate-600 hover:text-slate-400 transition-colors"
          >
            Rescan System
          </button>
        </div>
      )}

      {ingestProgress && (
        <div className="mt-6 rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
          <div className="mb-3 flex justify-between text-[10px] uppercase tracking-widest text-cyan-400">
            <span>{ingestProgress.label}</span>
            <span>{Math.round((ingestProgress.current / ingestProgress.total) * 100)}%</span>
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-slate-800">
            <div 
              className="h-full bg-cyan-500 transition-all duration-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]" 
              style={{ width: `${(ingestProgress.current / ingestProgress.total) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
