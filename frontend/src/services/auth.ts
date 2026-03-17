import { api } from "@/services/api";
import type { User, UserRole } from "@/types";

interface RoleLoginPayload {
  role: UserRole;
  email?: string;
  name?: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface RefreshResponse {
  access_token: string;
  token_type: string;
}

interface GoogleAuthorizeResponse {
  authorization_url: string;
}

interface GoogleTokenExchangePayload {
  code: string;
  redirect_uri?: string;
}

interface GoogleTokenExchangeResponse {
  connected: boolean;
  expires_in?: number;
  scope?: string;
}

interface GoogleConnectionStatusResponse {
  connected: boolean;
  token_expiry?: string | null;
}

export const authService = {
  async roleLogin(payload: RoleLoginPayload) {
    const { data } = await api.post<TokenResponse>("/auth/role-login", payload);
    return data;
  },
  async me() {
    const { data } = await api.get<User>("/auth/me");
    return data;
  },
  async refresh(refreshToken: string) {
    const { data } = await api.post<RefreshResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return data;
  },
  async getGoogleAuthorizeUrl() {
    const { data } = await api.get<GoogleAuthorizeResponse>("/auth/google/authorize");
    return data;
  },
  async exchangeGoogleCode(payload: GoogleTokenExchangePayload) {
    const { data } = await api.post<GoogleTokenExchangeResponse>("/auth/google/exchange", payload);
    return data;
  },
  async getGoogleConnectionStatus() {
    const { data } = await api.get<GoogleConnectionStatusResponse>("/auth/google/status");
    return data;
  },
};
