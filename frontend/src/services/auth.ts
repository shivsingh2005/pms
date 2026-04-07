import { api } from "@/services/api";
import type { User, UserRole } from "@/types";

interface LoginPayload {
  email: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    name: string;
    role: UserRole;
    email?: string;
    roles?: UserRole[];
    manager_id?: string | null;
    domain?: string | null;
    business_unit?: string | null;
    department?: string | null;
    title?: string | null;
    first_login?: boolean;
    onboarding_complete?: boolean;
    last_active?: string | null;
  };
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
  async login(payload: LoginPayload) {
    const cleanedEmail = payload.email.trim().toLowerCase();
    const { data } = await api.post<TokenResponse>("/auth/login", { email: cleanedEmail });
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
  async getGoogleAuthorizeUrl(redirectTo = "/meetings") {
    const { data } = await api.get<GoogleAuthorizeResponse>("/auth/google/authorize", {
      params: { redirect_to: redirectTo },
    });
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
  async completeOnboarding() {
    await api.post("/auth/onboarding/complete");
  },
};
