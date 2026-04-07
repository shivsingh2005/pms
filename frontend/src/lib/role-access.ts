import type { UserRole } from "@/types";

export function resolveDefaultRouteForRole(role: UserRole): string {
  if (role === "employee") return "/employee/dashboard";
  if (role === "manager") return "/manager/dashboard";
  if (role === "hr") return "/hr/dashboard";
  return "/leadership/dashboard";
}

const roleRoutePrefixes: Record<UserRole, string[]> = {
  employee: ["/employee", "/employee-dashboard", "/goals", "/checkins", "/meetings", "/reviews"],
  manager: ["/manager", "/manager-dashboard", "/employee", "/employee-dashboard", "/goals", "/checkins", "/meetings", "/reviews"],
  hr: ["/hr", "/hr-dashboard"],
  leadership: ["/leadership", "/dashboard", "/goals", "/checkins", "/meetings", "/reviews"],
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
