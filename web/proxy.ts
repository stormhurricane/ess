import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE, verifySessionToken } from "@/lib/session";

function withNoStore(response: NextResponse): NextResponse {
  response.headers.set(
    "Cache-Control",
    "private, no-store, no-cache, must-revalidate",
  );
  response.headers.set("Pragma", "no-cache");
  response.headers.set("Vary", "Cookie, Authorization");
  return response;
}

function loginRedirect(request: NextRequest): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  const next = request.nextUrl.pathname + request.nextUrl.search;
  if (next && next !== "/login") {
    url.searchParams.set("next", next);
  }
  return withNoStore(NextResponse.redirect(url));
}

function apiUnauthorized(): NextResponse {
  // No WWW-Authenticate — avoids iOS Safari Basic-Auth hang on fetch.
  return withNoStore(
    NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    ),
  );
}

function checkBasicAuth(
  header: string | null,
  user: string,
  password: string,
): boolean {
  if (!header?.startsWith("Basic ")) return false;
  let decoded: string;
  try {
    decoded = atob(header.slice("Basic ".length));
  } catch {
    return false;
  }
  const colon = decoded.indexOf(":");
  if (colon === -1) return false;
  return (
    decoded.slice(0, colon) === user && decoded.slice(colon + 1) === password
  );
}

export async function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;

  if (
    path === "/api/health" ||
    path === "/login" ||
    path === "/api/login"
  ) {
    return withNoStore(NextResponse.next());
  }

  const user = process.env.BASIC_AUTH_USER?.trim();
  const password = process.env.BASIC_AUTH_PASSWORD?.trim();

  if (!user || !password) {
    if (process.env.NODE_ENV === "development") {
      return NextResponse.next();
    }
    return withNoStore(
      new NextResponse("Basic auth is not configured", { status: 500 }),
    );
  }

  const session = request.cookies.get(SESSION_COOKIE)?.value;
  if (session && (await verifySessionToken(session, user))) {
    return withNoStore(NextResponse.next());
  }

  if (checkBasicAuth(request.headers.get("authorization"), user, password)) {
    return withNoStore(NextResponse.next());
  }

  if (path.startsWith("/api/")) {
    return apiUnauthorized();
  }

  return loginRedirect(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
