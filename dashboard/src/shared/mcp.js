const CACHE_TTL = 60 * 60 * 1000; // 1 hour
const cache = new Map();

/**
 * Call an MCP tool via the SSE endpoint with client-side caching.
 */
export async function callMCPTool(toolName, args = {}) {
  const cacheKey = `${toolName}:${JSON.stringify(args)}`;
  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  const res = await fetch(`/api/mcp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool: toolName, arguments: args }),
  });

  if (!res.ok) {
    throw new Error(`MCP call failed: ${res.status}`);
  }

  const data = await res.json();

  cache.set(cacheKey, {
    data,
    timestamp: Date.now(),
  });

  return data;
}

/**
 * Invalidate cache for a specific patient so next fetch is fresh.
 */
export function invalidatePatientCache(patientId) {
  for (const key of cache.keys()) {
    if (key.includes(patientId) || key.includes("get_ward_round_summary") || key.includes("get_conflict_report") || key.includes("get_discharge_candidates")) {
      cache.delete(key);
    }
  }
}

/**
 * Clear all cache.
 */
export function clearMCPCache() {
  cache.clear();
}
