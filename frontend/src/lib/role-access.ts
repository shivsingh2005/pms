import type { UserRole } from "@/types";

export function resolveDefaultRouteForRole(role: UserRole): string {
  if (role === "employee") return "/employee-dashboard";
  if (role === "manager") return "/manager-dashboard";
  if (role === "hr") return "/hr-dashboard";
  if (role === "leadership") return "/leadership/org-dashboard";
  return "/admin/dashboard";
}

const commonPrefixes = ["/dashboard", "/goals", "/checkins", "/meetings", "/reviews"];

const roleRoutePrefixes: Record<UserRole, string[]> = {
  employee: ["/employee", "/employee-dashboard", ...commonPrefixes],
  manager: ["/manager", "/manager-dashboard", ...commonPrefixes],
  hr: ["/hr", "/hr-dashboard", ...commonPrefixes],
  leadership: ["/leadership", ...commonPrefixes],
  admin: ["/admin", ...commonPrefixes],
};

const authFreeRoutes = ["/", "/auth", "/unauthorized"];

export function isAuthFreePath(pathname: string): boolean {
  return authFreeRoutes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function isPathAllowedForRole(pathname: string, role: UserRole): boolean {
  if (isAuthFreePath(pathname)) {
    return true;
  }

  const allowedPrefixes = roleRoutePrefixes[role] ?? [];
  return allowedPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}
