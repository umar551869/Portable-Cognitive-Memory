import { useEffect, useMemo, useState } from "react";
import GraphView from "./components/GraphView";
import NodeDetailsPanel from "./components/NodeDetailsPanel";
import SearchBar from "./components/SearchBar";
import AuthPage from "./components/AuthPage";
import SystemSyncPanel from "./components/SystemSyncPanel";
import IngestModal from "./components/IngestModal";
import ErrorBoundary from "./components/ErrorBoundary";
import { fetchGraph, recall } from "./api";

const STORAGE_KEY = "pcg_session";

function loadStoredSession() {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

export default function App() {
  const [session, setSession] = useState(() => loadStoredSession());
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState(new Set());
  const [searchMeta, setSearchMeta] = useState(null);
  const [searchRawLogs, setSearchRawLogs] = useState([]);
  const [searchPulse, setSearchPulse] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [graphError, setGraphError] = useState("");
  const [isIngestOpen, setIsIngestOpen] = useState(false);

  useEffect(() => {
    if (!session?.token) {
      return;
    }

    let isActive = true;
    async function loadGraph() {
      setIsLoadingGraph(true);
      setGraphError("");
      try {
        const payload = await fetchGraph(session.token);
        if (!isActive) {
          return;
        }
        setGraphData(payload);
        setHighlightedNodeIds(new Set(payload.nodes.map((node) => node.id)));
      } catch (error) {
        if (!isActive) {
          return;
        }
        setGraphError(error.message);
        if (error.message.includes("Invalid authentication")) {
          setSession(null);
        }
      } finally {
        if (isActive) {
          setIsLoadingGraph(false);
        }
      }
    }

    loadGraph();
    return () => {
      isActive = false;
    };
  }, [session]);

  useEffect(() => {
    if (session) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }, [session]);

  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return graphData.nodes.find((node) => String(node.id) === String(selectedNodeId)) || null;
  }, [graphData.nodes, selectedNodeId]);

  const connectedLinks = useMemo(() => {
    if (!selectedNodeId) return [];
    const selId = String(selectedNodeId);
    return graphData.links.filter((link) => {
      const sourceId = String(typeof link.source === "object" ? link.source.id : link.source);
      const targetId = String(typeof link.target === "object" ? link.target.id : link.target);
      return sourceId === selId || targetId === selId;
    });
  }, [graphData.links, selectedNodeId]);

  const connectedNodes = useMemo(() => {
    if (!selectedNodeId) return [];
    const selId = String(selectedNodeId);
    const ids = new Set();
    for (const link of connectedLinks) {
      const sourceId = String(typeof link.source === "object" ? link.source.id : link.source);
      const targetId = String(typeof link.target === "object" ? link.target.id : link.target);
      if (sourceId !== selId) ids.add(sourceId);
      if (targetId !== selId) ids.add(targetId);
    }
    return graphData.nodes.filter((node) => ids.has(String(node.id)));
  }, [connectedLinks, graphData.nodes, selectedNodeId]);

  async function handleSearch(query) {
    if (!session?.token) {
      return;
    }
    setIsSearching(true);
    setGraphError("");
    try {
      const payload = await recall(query, session.token);
      const matchedIds = new Set(payload.nodes.map((node) => node.id));
      setHighlightedNodeIds(matchedIds);
      setSearchRawLogs(payload.rawLogs || []);
      setSearchMeta({
        query: payload.query,
        matchCount: payload.nodes.length,
        rawLogCount: payload.rawLogs.length
      });
      if (payload.nodes.length) {
        setSelectedNodeId(payload.nodes[0].id);
      }
      setSearchPulse((value) => value + 1);
    } catch (error) {
      setGraphError(error.message);
      if (error.message.includes("Invalid authentication")) {
        setSession(null);
      }
    } finally {
      setIsSearching(false);
    }
  }

  function handleResetFocus() {
    setSelectedNodeId(null);
    setSearchRawLogs([]);
    setSearchMeta(null);
    setHighlightedNodeIds(new Set(graphData.nodes.map((node) => node.id)));
  }

  function handleNodeSelect(node) {
    setSelectedNodeId(node?.id || null);
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-950 font-sans text-slate-200">
        <AuthPage onLoginSuccess={setSession} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 font-sans text-slate-200">
      <div className="relative flex h-screen w-full flex-col overflow-hidden">
        <header className="panel-backdrop sticky top-0 z-20 flex flex-col gap-4 border-b border-slate-800/80 bg-slate-950/85 px-6 py-4 shadow-glow backdrop-blur xl:flex-row xl:items-center xl:justify-between">
          <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                <div className="h-4 w-4 animate-pulse rounded-full bg-current" />
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.35em] text-cyan-400">
                  Neural Identity Linked: {session?.user?.name || "Explorer"}
                </p>
                <h1 className="mt-1 font-display text-3xl text-white lg:text-4xl">
                  Portable <span className="text-cyan-400">Cognitive</span> Graph
                </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsIngestOpen(true)}
              className="rounded-xl bg-cyan-500 px-5 py-2.5 text-xs font-bold uppercase tracking-widest text-slate-950 transition-all hover:bg-cyan-400"
            >
              Neural Ingest
            </button>
            <button
              onClick={() => setSession(null)}
              className="rounded-xl border border-slate-800 bg-slate-900/50 px-5 py-2.5 text-xs font-bold uppercase tracking-widest text-slate-400 transition-all hover:border-rose-500/50 hover:bg-rose-500/10 hover:text-rose-400"
            >
              Terminate Link
            </button>
          </div>
        </header>


        <div className="grid flex-1 grid-cols-1 lg:min-h-0 lg:grid-cols-[420px_minmax(0,1fr)]">
          {/* Left Column: Intelligence Sidebar */}
          <div className="scroll-thin flex flex-col gap-5 overflow-y-auto border-b border-slate-800/80 bg-slate-950/20 px-4 py-4 lg:border-b-0 lg:border-r lg:px-6 lg:py-6">
            <SearchBar 
              onSearch={handleSearch} 
              isSearching={isSearching} 
              onReset={handleResetFocus} 
              searchMeta={searchMeta}
            />
            <SystemSyncPanel 
              token={session.token} 
              onIngestSuccess={() => setSearchPulse(p => p + 1)} 
            />
            <NodeDetailsPanel 
              node={selectedNode}
              connectedNodes={connectedNodes}
              relatedLinks={connectedLinks}
              rawLogs={searchRawLogs}
            />
          </div>

          {/* Right Column: Neural Graph */}
          <div className="relative flex min-h-[32rem] h-full w-full flex-col overflow-hidden lg:min-h-0">
            <ErrorBoundary>
              <GraphView
                graphData={graphData}
                selectedNodeId={selectedNodeId}
                highlightedNodeIds={highlightedNodeIds}
                onNodeSelect={handleNodeSelect}
                searchPulse={searchPulse}
              />
            </ErrorBoundary>
            {isLoadingGraph && (
              <div className="pointer-events-none absolute left-8 top-8 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-4 py-2 text-sm text-cyan-100">
                Loading graph...
              </div>
            )}
            {graphError && (
              <div className="absolute bottom-8 left-8 right-8 rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                {graphError}
              </div>
            )}
          </div>
        </div>
      </div>

      {isIngestOpen && (
        <IngestModal 
          token={session.token} 
          onClose={() => setIsIngestOpen(false)} 
          onIngestSuccess={() => {
            // Optionally refresh graph
            setSearchPulse(p => p + 1);
          }}
        />
      )}
    </div>
  );
}
