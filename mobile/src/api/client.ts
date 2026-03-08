import type {
  ApiMessage,
  AuthResponse,
  AuthUser,
  IngestMessagesPayload,
  IngestMessagesResponse,
  LoginPayload,
  RegisterPayload,
  SummaryResponse,
} from "./types";
import { Platform } from "react-native";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function stringifyValidationDetail(detail: unknown): string | null {
  if (typeof detail === "string") {
    const text = detail.trim();
    return text || null;
  }

  if (Array.isArray(detail)) {
    const lines = detail
      .map((item) => {
        if (!item || typeof item !== "object") return null;

        const msg = "msg" in item && typeof item.msg === "string" ? item.msg : null;
        const locParts =
          "loc" in item && Array.isArray(item.loc)
            ? item.loc.map((x: unknown) => String(x)).filter((x: string) => x !== "body")
            : [];
        const loc = locParts.length ? locParts.join(".") : null;

        if (msg && loc) return `${loc}: ${msg}`;
        if (msg) return msg;
        return null;
      })
      .filter((line): line is string => Boolean(line));

    if (lines.length) return lines.join("; ");
    return null;
  }

  if (detail && typeof detail === "object") {
    if ("detail" in detail) {
      const nested = stringifyValidationDetail(detail.detail);
      if (nested) return nested;
    }
    if ("message" in detail && typeof detail.message === "string") {
      const text = detail.message.trim();
      if (text) return text;
    }
  }

  return null;
}

export function normalizeApiBase(value: string): string {
  let normalized = String(value || "")
    .trim()
    .replace(/\/+$/, "");

  if (!normalized) return "";

  if (!/^[a-zA-Z][a-zA-Z\d+\-.]*:\/\//.test(normalized)) {
    normalized = `http://${normalized}`;
  }

  try {
    const url = new URL(normalized);
    const localHosts = new Set(["127.0.0.1", "localhost", "10.0.2.2"]);
    if (!url.port && localHosts.has(url.hostname)) {
      url.port = "8000";
      normalized = url.toString().replace(/\/$/, "");
    }
  } catch {
    // Keep original string; fetch will surface any invalid URL issues.
  }

  return normalized;
}

type RequestOptions = {
  apiBase: string;
  path: string;
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  token?: string | null;
  body?: unknown;
};

async function request<T>({
  apiBase,
  path,
  method = "GET",
  token,
  body,
}: RequestOptions): Promise<T> {
  const normalized = normalizeApiBase(apiBase);
  if (!normalized) {
    throw new Error("API base URL is required.");
  }

  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const tryFetch = async (base: string) =>
    fetch(`${base}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });

  const fallbackBases = new Set<string>();
  if (Platform.OS === "android") {
    // Emulator fallback(s).
    fallbackBases.add(normalizeApiBase(normalized.replace("://127.0.0.1", "://10.0.2.2")));
    fallbackBases.add(normalizeApiBase(normalized.replace("://localhost", "://10.0.2.2")));

    // Physical-device-over-USB fallback(s) when adb reverse is active.
    fallbackBases.add(normalizeApiBase(normalized.replace("://10.0.2.2", "://127.0.0.1")));
    fallbackBases.add(normalizeApiBase(normalized.replace("://localhost", "://127.0.0.1")));

    const withSamePort = normalized.match(/^https?:\/\/(?:\d{1,3}\.){3}\d{1,3}:(\d+)$/);
    if (withSamePort) {
      fallbackBases.add(`http://10.0.2.2:${withSamePort[1]}`);
      fallbackBases.add(`http://127.0.0.1:${withSamePort[1]}`);
    }
  }
  fallbackBases.delete(normalized);
  fallbackBases.delete("");

  let response: Response | null = null;
  let lastNetworkError: unknown = null;
  const triedBases: string[] = [];
  for (const base of [normalized, ...fallbackBases]) {
    triedBases.push(base);
    try {
      response = await tryFetch(base);
      break;
    } catch (error) {
      lastNetworkError = error;
    }
  }

  if (!response) {
    void lastNetworkError;
    throw new Error(
      [
        `Could not reach API at ${normalized}.`,
        `Tried: ${triedBases.join(", ")}`,
        "Make sure the backend is running and reachable from your device.",
        "USB mode (Android physical phone): run adb reverse tcp:8000 tcp:8000",
        "Check reverse mappings: adb reverse --list",
        "Android emulator: use http://10.0.2.2:8000",
        "iOS simulator: use http://127.0.0.1:8000",
        "Real phone: use your computer LAN IP, e.g. http://192.168.1.24:8000",
        "Start backend with: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000",
      ].join(" "),
    );
  }

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.toLowerCase().includes("application/json");

  let payload: unknown = null;
  if (isJson) {
    payload = await response.json().catch(() => null);
  } else {
    payload = await response.text().catch(() => "");
  }

  if (!response.ok) {
    const parsedDetail = stringifyValidationDetail(payload);
    const message = parsedDetail || `${response.status} ${response.statusText}`;
    throw new ApiError(message, response.status);
  }

  return payload as T;
}

export function checkHealth(apiBase: string): Promise<ApiMessage> {
  return request<ApiMessage>({ apiBase, path: "/" });
}

export function registerUser(apiBase: string, payload: RegisterPayload): Promise<AuthResponse> {
  return request<AuthResponse>({
    apiBase,
    path: "/auth/register",
    method: "POST",
    body: payload,
  });
}

export function loginUser(apiBase: string, payload: LoginPayload): Promise<AuthResponse> {
  return request<AuthResponse>({
    apiBase,
    path: "/auth/login",
    method: "POST",
    body: payload,
  });
}

export function getCurrentUser(apiBase: string, token: string): Promise<AuthUser> {
  return request<AuthUser>({
    apiBase,
    path: "/auth/me",
    token,
  });
}

export function getSummary(apiBase: string, token: string): Promise<SummaryResponse> {
  return request<SummaryResponse>({
    apiBase,
    path: "/summary",
    token,
  });
}

export function ingestMessages(
  apiBase: string,
  token: string,
  payload: IngestMessagesPayload,
): Promise<IngestMessagesResponse> {
  return request<IngestMessagesResponse>({
    apiBase,
    path: "/ingestion/messages",
    method: "POST",
    token,
    body: payload,
  });
}
