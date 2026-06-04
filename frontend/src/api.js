const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

async function request(path, options = {}) {
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...(Object.keys(headers).length ? { headers } : {}),
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep the generic error when the server does not return JSON.
    }
    throw new Error(detail);
  }

  return response.json();
}

export function getHealth() {
  return request("/health");
}

export function getNotifications() {
  return request("/notifications");
}

export function runAgentOnce() {
  return request("/agent/run-once", { method: "POST" });
}
