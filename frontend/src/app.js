// Override at runtime in the browser console if you want:
// window.MPESA_API_BASE = "http://127.0.0.1:8000";
function isPrivateLanHost(host) {
  const value = String(host || "").toLowerCase();
  if (!value) return false;
  if (value === "localhost" || value === "127.0.0.1" || value === "0.0.0.0" || value === "[::1]") {
    return true;
  }
  if (/^10(?:\.\d{1,3}){3}$/.test(value)) return true;
  if (/^192\.168(?:\.\d{1,3}){2}$/.test(value)) return true;
  return /^172\.(1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}$/.test(value);
}

function resolveDefaultApiBase() {
  if (window.location.protocol === "file:") return "http://127.0.0.1:8000";
  const host = (window.location.hostname || "").toLowerCase();
  if (isPrivateLanHost(host)) {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return `${window.location.origin}/api`;
}

function normalizeApiBase(value) {
  return String(value || "")
    .trim()
    .replace(/\/+$/, "");
}

const API_BASE = normalizeApiBase(
  window.MPESA_API_BASE ?? localStorage.getItem("MPESA_API_BASE") ?? resolveDefaultApiBase(),
);
const DEFAULT_API_BASE = normalizeApiBase(resolveDefaultApiBase());
let currentApiBase = API_BASE;
let apiToken = (window.MPESA_API_TOKEN ?? localStorage.getItem("MPESA_API_TOKEN") ?? "").trim();

function byId(id) {
  return document.getElementById(id);
}

function pretty(obj) {
  return JSON.stringify(obj, null, 2);
}

function formatNumber(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}

function formatCurrency(amount, currency = "KES") {
  if (typeof amount !== "number" || !Number.isFinite(amount)) return "—";
  return `${currency} ${formatNumber(amount)}`;
}

function formatDateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString();
}

async function apiFetch(path, init = {}) {
  const buildHeaders = () => {
    const headers = {
      ...(init.headers || {}),
    };
    if (apiToken) headers.Authorization = `Bearer ${apiToken}`;
    if (!headers["Content-Type"] && init.body) headers["Content-Type"] = "application/json";
    return headers;
  };

  const doFetch = (base) => fetch(`${base}${path}`, { ...init, headers: buildHeaders() });

  let res;
  try {
    res = await doFetch(currentApiBase);
  } catch {
    const canFallback = DEFAULT_API_BASE && DEFAULT_API_BASE !== currentApiBase;
    if (canFallback) {
      try {
        res = await doFetch(DEFAULT_API_BASE);
        currentApiBase = DEFAULT_API_BASE;
        localStorage.setItem("MPESA_API_BASE", DEFAULT_API_BASE);
      } catch {
        throw new Error(
          [
            `Network error contacting API at ${currentApiBase}.`,
            `Fallback to default API base (${DEFAULT_API_BASE}) also failed.`,
            `Make sure the backend is running (uvicorn backend.main:app --reload --port 8000).`,
            `If you're opening the UI via file://, serve it (cd frontend/src && python -m http.server 5173).`,
            `Set API base manually with: localStorage.setItem("MPESA_API_BASE","http://127.0.0.1:8000"); location.reload();`,
          ].join(" "),
        );
      }
    } else {
      throw new Error(
        [
          `Network error contacting API at ${currentApiBase}.`,
          `Make sure the backend is running (uvicorn backend.main:app --reload --port 8000).`,
          `If you're opening the UI via file://, serve it (cd frontend/src && python -m http.server 5173).`,
          `If the API is on another host/path, run: localStorage.setItem("MPESA_API_BASE","https://api.example.com"); location.reload();`,
        ].join(" "),
      );
    }
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail || data.error || data.message || `${res.status} ${res.statusText}`;
    if (res.status === 401) {
      throw new Error(`${detail} Open auth.html to sign in.`);
    }
    throw new Error(detail);
  }
  return data;
}

function apiGet(path) {
  return apiFetch(path);
}

function apiPost(path, body) {
  return apiFetch(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

function apiDelete(path) {
  return apiFetch(path, { method: "DELETE" });
}

function apiPatch(path, body) {
  return apiFetch(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

function apiPut(path, body) {
  return apiFetch(path, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

function setText(id, text) {
  const node = byId(id);
  if (!node) return;
  node.textContent = text;
}

function setHtml(id, html) {
  const node = byId(id);
  if (!node) return;
  node.innerHTML = html;
}

function setApiIndicator({ online, text }) {
  const pill = byId("apiPill");
  const dot = byId("apiDot");
  const label = byId("apiText");
  if (!pill || !dot || !label) return;

  label.textContent = text;

  pill.classList.remove("text-bg-secondary", "text-bg-success", "text-bg-danger", "text-bg-warning");
  if (online === true) pill.classList.add("text-bg-success");
  else if (online === false) pill.classList.add("text-bg-danger");
  else pill.classList.add("text-bg-secondary");

  if (online === true) dot.style.background = "rgba(25, 135, 84, 0.95)";
  else if (online === false) dot.style.background = "rgba(220, 53, 69, 0.95)";
  else dot.style.background = "rgba(26, 123, 74, 0.35)";
}

async function checkApi() {
  setApiIndicator({ online: null, text: "API: checking…" });
  try {
    const data = await apiGet("/");
    setApiIndicator({ online: true, text: "API: online" });
    return data;
  } catch {
    setApiIndicator({ online: false, text: "API: offline" });
    return null;
  }
}

// Expose minimal API helpers for other pages (e.g., budget.html).
window.mpesaApi = window.mpesaApi ?? {};
Object.defineProperty(window.mpesaApi, "base", {
  configurable: true,
  get() {
    return currentApiBase;
  },
});
window.mpesaApi.setBase = (base) => {
  const normalized = normalizeApiBase(base);
  if (normalized) {
    currentApiBase = normalized;
    localStorage.setItem("MPESA_API_BASE", normalized);
  } else {
    currentApiBase = DEFAULT_API_BASE;
    localStorage.removeItem("MPESA_API_BASE");
  }
};

window.mpesaApi.getToken = () => apiToken;
window.mpesaApi.setToken = (token) => {
  apiToken = String(token || "").trim();
  if (apiToken) {
    localStorage.setItem("MPESA_API_TOKEN", apiToken);
  } else {
    localStorage.removeItem("MPESA_API_TOKEN");
  }
};
window.mpesaApi.clearToken = () => window.mpesaApi.setToken("");
window.mpesaApi.logout = () => window.mpesaApi.clearToken();

window.mpesaApi.register = async (payload) => {
  const data = await apiPost("/auth/register", payload);
  if (data?.access_token) window.mpesaApi.setToken(data.access_token);
  return data;
};
window.mpesaApi.login = async (payload) => {
  const data = await apiPost("/auth/login", payload);
  if (data?.access_token) window.mpesaApi.setToken(data.access_token);
  return data;
};
window.mpesaApi.me = () => apiGet("/auth/me");

window.mpesaApi.get = apiGet;
window.mpesaApi.post = apiPost;
window.mpesaApi.put = apiPut;
window.mpesaApi.patch = apiPatch;
window.mpesaApi.del = apiDelete;
window.mpesaApi.check = checkApi;
