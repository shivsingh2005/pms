import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedRoutes = ["/dashboard", "/goals", "/checkins", "/meetings", "/reviews"];

export function middleware(request: NextRequest) {
  const token = request.cookies.get("pms_token")?.value;
  const { pathname } = request.nextUrl;

  const isProtected = protectedRoutes.some((route) => pathname.startsWith(route));

  if (isProtected && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/goals/:path*", "/checkins/:path*", "/meetings/:path*", "/reviews/:path*"],
};
