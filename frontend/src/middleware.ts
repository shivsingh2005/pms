import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

type UserRole = "employee" | "manager" | "hr" | "leadership" | "admin";

const protectedRoutes = [
  "/employee/dashboard",
  "/manager/dashboard",
  "/hr/dashboard",
  "/leadership/dashboard",
  "/employee-dashboard",
  "/dashboard",
  "/manager-dashboard",
  "/manager",
  "/goals",
  "/checkins",
  "/meetings",
  "/reviews",
  "/hr-dashboard",
  "/hr",
  "/leadership",
  "/admin",
];

const roleHomeRoute: Record<UserRole, string> = {
  employee: "/employee-dashboard",
  manager: "/manager-dashboard",
  hr: "/hr-dashboard",
  leadership: "/leadership/org-dashboard",
  admin: "/admin/dashboard",
};

const roleRoutePrefixes: Record<UserRole, string[]> = {
  employee: ["/employee", "/employee-dashboard", "/dashboard", "/goals", "/checkins", "/meetings", "/reviews"],
  manager: ["/manager", "/manager-dashboard", "/dashboard", "/goals", "/checkins", "/meetings", "/reviews"],
  hr: ["/hr", "/hr-dashboard", "/dashboard", "/goals", "/checkins", "/meetings", "/reviews"],
  leadership: ["/leadership", "/dashboard", "/goals", "/checkins", "/meetings", "/reviews"],
  admin: ["/admin", "/dashboard", "/goals", "/checkins", "/meetings", "/reviews"],
};

function decodeTokenRole(token: string): UserRole | null {
  try {
    const payloadSegment = token.split(".")[1];
    if (!payloadSegment) {
      return null;
    }

    const normalized = payloadSegment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const payload = JSON.parse(Buffer.from(padded, "base64").toString("utf-8")) as { role?: unknown };
    if (typeof payload.role !== "string") {
      return null;
    }

    const role = payload.role as UserRole;
    return role in roleRoutePrefixes ? role : null;
  } catch {
    return null;
  }
}

function isPathAllowedForRole(pathname: string, role: UserRole): boolean {
  const allowedPrefixes = roleRoutePrefixes[role] ?? [];
  return allowedPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function middleware(request: NextRequest) {
  const token = request.cookies.get("pms_token")?.value;
  const { pathname } = request.nextUrl;

  const isProtected = protectedRoutes.some((route) => pathname.startsWith(route));

  if (isProtected && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/";
    return NextResponse.redirect(url);
  }

  if (!isProtected || !token) {
    return NextResponse.next();
  }

  const role = decodeTokenRole(token);
  if (role && !isPathAllowedForRole(pathname, role)) {
    const url = request.nextUrl.clone();
    url.pathname = roleHomeRoute[role];
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/employee-dashboard/:path*",
    "/employee/dashboard/:path*",
    "/dashboard/:path*",
    "/manager-dashboard/:path*",
    "/manager/dashboard/:path*",
    "/manager/:path*",
    "/goals/:path*",
    "/checkins/:path*",
    "/meetings/:path*",
    "/reviews/:path*",
    "/hr-dashboard/:path*",
    "/hr/dashboard/:path*",
    "/hr/:path*",
    "/leadership/:path*",
    "/leadership/dashboard/:path*",
    "/admin/:path*",
  ],
};
