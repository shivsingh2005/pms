import axios from "axios";
import { authCookies } from "@/lib/cookies";
import { toast } from "sonner";

const rawApiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_BASE_URL = rawApiUrl.endsWith("/api/v1") ? rawApiUrl : `${rawApiUrl.replace(/\/$/, "")}/api/v1`;

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
    const requestUrl = error?.config?.url ? `${API_BASE_URL}${error.config.url}` : API_BASE_URL;
    const isNetworkError = !error?.response && error?.message === "Network Error";

    if (isNetworkError) {
      toast.error(`Cannot reach backend API at ${requestUrl}. Ensure backend is running and CORS origin is allowed.`);
      return Promise.reject(error);
    }

    const detail =
      error?.response?.data?.error ||
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "Request failed";

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
