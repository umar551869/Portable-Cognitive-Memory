const DEFAULT_API_BASE = "http://127.0.0.1:8000";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || DEFAULT_API_BASE;

async function request(path, { method = "GET", body, token } = {}) {
  const headers = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message = payload?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

export async function login(credentials) {
  return request("/auth/login", { method: "POST", body: credentials });
}

export async function registerAccount(payload) {
  return request("/auth/register", { method: "POST", body: payload });
}

export async function fetchGraph(token) {
  const payload = await request("/graph", { token });
  return {
    nodes: (payload?.nodes || []).map((node) => ({
      id: node.id,
      name: node.display_name || node.canonical_name || node.id,
      canonicalName: node.canonical_name || node.display_name || node.id,
      type: node.type || "unknown",
      weight: node.weight || 1,
      description: node.description || "",
      metadata: node.metadata || {},
      aliases: node.aliases || [],
      score: node.score || 0
    })),
    links: (payload?.edges || []).map((edge) => ({
      source: edge.source_id,
      target: edge.target_id,
      relation: edge.relation || "related",
      weight: edge.weight || 1,
      evidence: edge.evidence || ""
    }))
  };
}

export async function recall(query, token) {
  const payload = await request(`/recall?q=${encodeURIComponent(query)}`, {
    token
  });
  return {
    query: payload?.query || query,
    nodes: (payload?.nodes || []).map((node) => ({
      id: node.id,
      name: node.display_name || node.canonical_name || node.id,
      canonicalName: node.canonical_name || node.display_name || node.id,
      type: node.type || "unknown",
      weight: node.weight || 1,
      description: node.description || "",
      metadata: node.metadata || {},
      aliases: node.aliases || [],
      score: node.score || 0
    })),
    links: (payload?.edges || []).map((edge) => ({
      source: edge.source_id,
      target: edge.target_id,
      relation: edge.relation || "related",
      weight: edge.weight || 1,
      evidence: edge.evidence || ""
    })),
    rawLogs: payload?.raw_logs || []
  };
}

export async function ingestDirectory(path, projectId, token) {
  return request("/ingest-directory", {
    method: "POST",
    body: { path, project_id: projectId },
    token
  });
}

export async function ingestText(content, sourcePath, projectId, token) {
  return request("/ingest", {
    method: "POST",
    body: { content, source_path: sourcePath, project_id: projectId },
    token
  });
}

export async function scanSystem(token) {
  return request("/discovery/scan", { token });
}

export async function watchSystem(token) {
  return request("/discovery/watch", { method: "POST", token });
}

export { API_BASE };
