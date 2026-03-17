import axios from "axios";
import { authCookies } from "@/lib/cookies";
import { toast } from "sonner";

function normalizeErrorMessage(value: unknown): string {
  if (typeof value === "string" && value.trim()) {
    return value;
  }

  if (Array.isArray(value) && value.length > 0) {
    const first = value[0] as { msg?: unknown; loc?: unknown };
    const msg = typeof first?.msg === "string" ? first.msg : "Validation failed";
    const loc = Array.isArray(first?.loc) ? first.loc.join(".") : "";
    return loc ? `${msg} (${loc})` : msg;
  }

  if (value && typeof value === "object") {
    const rec = value as Record<string, unknown>;
    if (typeof rec.msg === "string" && rec.msg.trim()) {
      return rec.msg;
    }
    if (typeof rec.detail === "string" && rec.detail.trim()) {
      return rec.detail;
    }
    return "Request failed";
  }

  return "Request failed";
}

const rawApiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const resolvedExternalApiBase = rawApiUrl.endsWith("/api/v1") ? rawApiUrl : `${rawApiUrl.replace(/\/$/, "")}/api/v1`;

// Use same-origin proxy in the browser to avoid CORS and localhost/LAN host mismatches.
const API_BASE_URL = typeof window === "undefined" ? resolvedExternalApiBase : "/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = authCookies.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    const payload = response?.data;
    if (payload && typeof payload === "object" && "success" in payload) {
      return { ...response, data: payload.data };
    }
    return response;
  },
  async (error) => {
    const status = error?.response?.status;
    const requestUrl = error?.config?.url
      ? String(error.config.url).startsWith("http")
        ? String(error.config.url)
        : `${API_BASE_URL}${error.config.url}`
      : API_BASE_URL;
    const isNetworkError = !error?.response && error?.message === "Network Error";

    if (isNetworkError) {
      toast.error(`Cannot reach backend API at ${requestUrl}. Ensure backend is running and CORS origin is allowed.`);
      return Promise.reject(error);
    }

    const detail = normalizeErrorMessage(
      error?.response?.data?.error ??
      error?.response?.data?.detail ??
      error?.response?.data?.message ??
      error?.message,
    );

    const originalRequest = error?.config;

    if (status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true;
      const refreshToken = authCookies.getRefreshToken();
      if (refreshToken) {
        try {
          const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const refreshed = refreshResponse?.data?.data || refreshResponse?.data;
          authCookies.setToken(refreshed.access_token);
          originalRequest.headers.Authorization = `Bearer ${refreshed.access_token}`;
          return api(originalRequest);
        } catch {
          authCookies.clearToken();
          authCookies.clearRefreshToken();
        }
      }
    }

    if (status === 401) {
      authCookies.clearToken();
      authCookies.clearRefreshToken();
      if (typeof window !== "undefined") {
        window.location.href = "/";
      }
    }

    toast.error(detail);
    return Promise.reject(error);
  },
);
