const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `Request failed with status ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // response body wasn't JSON, keep the generic message
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

export function listInterviews() {
  return request("/interviews");
}

export function startInterview(topic) {
  return request("/interviews", { method: "POST", body: JSON.stringify({ topic }) });
}

export function submitAnswer(interviewId, answer) {
  return request(`/interviews/${interviewId}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });
}

export function getInterview(interviewId) {
  return request(`/interviews/${interviewId}`);
}

export function getSummary(interviewId) {
  return request(`/interviews/${interviewId}/summary`);
}

export function exportJsonUrl(interviewId) {
  return `${API_BASE}/interviews/${interviewId}/export/json`;
}

export function exportPdfUrl(interviewId) {
  return `${API_BASE}/interviews/${interviewId}/export/pdf`;
}
