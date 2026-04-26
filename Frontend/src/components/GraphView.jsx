import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph3D from "react-force-graph-3d";
import * as THREE from "three";

const TYPE_COLORS = {
  concept:  "#00f2ff",
  process:  "#00ff8c",
  decision: "#ffb86c",
  artifact: "#bd93f9",
  unknown:  "#7c8cf8"
};

const IGNORE_RELATIONS = new Set(["uses", "has", "contains", "connects"]);

function getColor(type) {
  return TYPE_COLORS[type?.toLowerCase()] || TYPE_COLORS.unknown;
}

function buildAdjacency(links) {
  const m = new Map();
  if (!links) return m;
  for (const l of links) {
    const s = String(typeof l.source === "object" ? l.source.id : l.source);
    const t = String(typeof l.target === "object" ? l.target.id : l.target);
    if (!m.has(s)) m.set(s, new Set());
    if (!m.has(t)) m.set(t, new Set());
    m.get(s).add(t);
    m.get(t).add(s);
  }
  return m;
}

export default function GraphView({ graphData, selectedNodeId, onNodeSelect, searchPulse }) {
  const graphRef     = useRef(null);
  const containerRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [dims, setDims] = useState({ width: 0, height: 0 });

  // Semantic filtering
  const filteredData = useMemo(() => ({
    nodes: graphData?.nodes || [],
    links: (graphData?.links || []).filter(
      (l) => !IGNORE_RELATIONS.has(l.relation?.toLowerCase())
    )
  }), [graphData]);

  const adjacency = useMemo(() => buildAdjacency(filteredData.links), [filteredData.links]);

  const focusNodeIds = useMemo(() => {
    if (!selectedNodeId) return new Set();
    const nb = adjacency.get(String(selectedNodeId)) || new Set();
    return new Set([String(selectedNodeId), ...nb]);
  }, [adjacency, selectedNodeId]);

  // ── Pre-create all materials ONCE (no per-frame allocation) ──────────────
  const materials = useMemo(() => {
    const m = {};
    Object.entries(TYPE_COLORS).forEach(([type, hex]) => {
      const col = new THREE.Color(hex);
      m[`${type}_on`] = new THREE.MeshPhongMaterial({
        color: col, transparent: true, opacity: 0.94,
        shininess: 110, emissive: col.clone().multiplyScalar(0.45),
        specular: new THREE.Color("#ffffff")
      });
      m[`${type}_off`] = new THREE.MeshPhongMaterial({
        color: col, transparent: true, opacity: 0.22,
        shininess: 40,  emissive: col.clone().multiplyScalar(0.08)
      });
    });
    return m;
  }, []); // created ONCE

  const sharedGeo = useMemo(() => new THREE.SphereGeometry(1, 24, 24), []);

  // ── nodeThreeObject — NO hoveredNode dep → no rebuild on mouse move ───────
  const nodeThreeObject = useMemo(() => (node) => {
    const focused  = focusNodeIds.size === 0 || focusNodeIds.has(String(node.id));
    const selected = String(node.id) === String(selectedNodeId);
    const type     = node.type?.toLowerCase() || "unknown";
    const key      = `${TYPE_COLORS[type] ? type : "unknown"}_${focused ? "on" : "off"}`;
    const mat      = materials[key];
    const group    = new THREE.Group();
    const base     = 7 + Math.min(node.weight || 1, 12) * 2;
    const scale    = base * (selected ? 2.0 : 1.0);
    const mesh     = new THREE.Mesh(sharedGeo, mat);
    mesh.scale.set(scale, scale, scale);
    group.add(mesh);

    if (selected) {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(scale * 1.4, scale * 1.7, 32),
        new THREE.MeshBasicMaterial({
          color: new THREE.Color(getColor(node.type)),
          side: THREE.DoubleSide, transparent: true, opacity: 0.5
        })
      );
      group.add(ring);
    }
    return group;
  }, [focusNodeIds, selectedNodeId, materials, sharedGeo]);

  // Resize
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    
    // Set initial size
    const initialRect = el.getBoundingClientRect();
    if (initialRect.width > 0) setDims({ width: initialRect.width, height: initialRect.height });

    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDims({ width, height });
        }
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Forces
  useEffect(() => {
    const g = graphRef.current;
    if (!g) return;
    g.d3Force("charge")?.strength(-120).distanceMax(400);
    g.d3Force("link")?.distance(110).strength(0.5);
    const c = g.d3Force("center");
    if (c) { c.x(0); c.y(0); c.z(0); c.strength(0.45); }
    const ctrl = g.controls?.();
    if (ctrl) { ctrl.autoRotate = true; ctrl.autoRotateSpeed = 0.55; }
    g.cameraPosition({ x: 0, y: 180, z: 720 }, { x: 0, y: 0, z: 0 }, 1000);
  }, [filteredData.nodes.length]);

  // Zoom to selected
  useEffect(() => {
    const g = graphRef.current;
    if (!g || !selectedNodeId) return;
    const n = filteredData.nodes.find((x) => String(x.id) === String(selectedNodeId));
    if (n?.x !== undefined) {
      g.cameraPosition({ x: n.x + 250, y: n.y + 120, z: n.z + 250 }, n, 1200);
    }
  }, [selectedNodeId, searchPulse, filteredData.nodes]);

  const isLinkOn = (link) => {
    const s = String(typeof link.source === "object" ? link.source.id : link.source);
    const t = String(typeof link.target === "object" ? link.target.id : link.target);
    return focusNodeIds.size === 0 || focusNodeIds.has(s) || focusNodeIds.has(t);
  };

  if (!filteredData.nodes.length) return (
    <div className="flex h-full items-center justify-center">
      <p className="animate-pulse text-xs uppercase tracking-[0.3em] text-slate-500">Initializing...</p>
    </div>
  );

  return (
    <div ref={containerRef} className="relative w-full h-full flex-1 overflow-hidden bg-slate-950/20">
      <div className="pointer-events-none absolute inset-0 bg-aurora" />
      <div className="pointer-events-none absolute inset-0 grid-noise opacity-40" />

      <ForceGraph3D
        ref={graphRef}
        graphData={filteredData}
        width={dims.width || undefined}
        height={dims.height || undefined}
        backgroundColor="rgba(0,0,0,0)"
        nodeThreeObject={nodeThreeObject}
        onNodeHover={setHoveredNode}
        onNodeClick={(node) => onNodeSelect(node)}
        d3AlphaDecay={0.015}
        d3VelocityDecay={0.32}
        linkOpacity={0.55}
        linkWidth={(l) => isLinkOn(l) ? 3.5 : 0.8}
        linkColor={(l) => isLinkOn(l) ? "rgba(0,230,255,0.9)" : "rgba(148,163,184,0.18)"}
        linkCurvature={0.15}
        linkDirectionalParticles={(l) => isLinkOn(l) ? 3 : 0}
        linkDirectionalParticleWidth={2.5}
        linkDirectionalParticleSpeed={0.007}
        linkDirectionalParticleColor={() => "#00f2ff"}
        showNavInfo={false}
      />

      {hoveredNode && (
        <div className="pointer-events-none absolute left-6 top-6 max-w-[240px] rounded-2xl border border-white/10 bg-slate-950/90 p-4 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="h-2.5 w-2.5 rounded-full flex-shrink-0"
              style={{ background: getColor(hoveredNode.type), boxShadow: `0 0 7px ${getColor(hoveredNode.type)}` }} />
            <p className="text-[10px] font-bold uppercase tracking-[0.28em] text-slate-400">{hoveredNode.type}</p>
          </div>
          <p className="font-display text-lg leading-tight text-white">{hoveredNode.name}</p>
          <div className="mt-3 flex gap-5 border-t border-white/10 pt-3">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-slate-500">Links</p>
              <p className="font-display text-base text-cyan-400">{adjacency.get(String(hoveredNode.id))?.size || 0}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-slate-500">Weight</p>
              <p className="font-display text-base text-emerald-400">{hoveredNode.weight}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
