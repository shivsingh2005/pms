import { create } from "zustand";
import type { User } from "@/types";

interface SessionState {
  user: User | null;
  googleAccessToken: string | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setGoogleAccessToken: (token: string | null) => void;
  logout: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  user: null,
  googleAccessToken: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: Boolean(user) }),
  setGoogleAccessToken: (googleAccessToken) => set({ googleAccessToken }),
  logout: () => set({ user: null, isAuthenticated: false, googleAccessToken: null }),
}));
