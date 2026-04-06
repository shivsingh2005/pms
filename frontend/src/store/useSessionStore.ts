import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

export type UserMode = "employee" | "manager";

function canUseMode(user: User | null, mode: UserMode): boolean {
  if (!user) return false;
  if (user.role !== "manager") {
    return false;
  }
  return mode === "manager" || mode === "employee";
}

function resolveDefaultMode(user: User): UserMode | null {
  if (user.role === "manager") return "manager";
  if (user.role === "employee") return "employee";
  return null;
}

interface SessionState {
  user: User | null;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  activeMode: UserMode | null;
  setUser: (user: User | null) => void;
  patchUser: (patch: Partial<User>) => void;
  setAuthLoading: (loading: boolean) => void;
  setActiveMode: (mode: UserMode) => void;
  logout: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isAuthLoading: true,
      activeMode: null,
      setUser: (user) => {
        if (!user) {
          set({ user: null, isAuthenticated: false, activeMode: null });
          return;
        }

        const previousMode = get().activeMode;
        const defaultMode = resolveDefaultMode(user);
        const nextMode = previousMode && canUseMode(user, previousMode) ? previousMode : defaultMode;

        set({ user, isAuthenticated: true, activeMode: nextMode });
      },
      patchUser: (patch) => {
        const current = get().user;
        if (!current) {
          return;
        }
        set({ user: { ...current, ...patch } });
      },
      setAuthLoading: (loading) => set({ isAuthLoading: loading }),
      setActiveMode: (mode) => {
        if (!canUseMode(get().user, mode)) {
          return;
        }
        set({ activeMode: mode });
      },
      logout: () => set({ user: null, isAuthenticated: false, activeMode: null, isAuthLoading: false }),
    }),
    {
      name: "pms-session-store",
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        activeMode: state.activeMode,
      }),
    },
  ),
);
