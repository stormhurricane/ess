import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

function unauthorized(): NextResponse {
  return new NextResponse("Authentication required", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="ESS", charset="UTF-8"',
    },
  });
}

export function proxy(request: NextRequest) {
  if (request.nextUrl.pathname === "/api/health") {
    return NextResponse.next();
  }

  const user = process.env.BASIC_AUTH_USER;
  const password = process.env.BASIC_AUTH_PASSWORD;

  if (!user || !password) {
    // Local `npm run dev` without secrets; fail closed in production.
    if (process.env.NODE_ENV === "development") {
      return NextResponse.next();
    }
    return new NextResponse("Basic auth is not configured", { status: 500 });
  }

  const header = request.headers.get("authorization");
  if (!header?.startsWith("Basic ")) {
    return unauthorized();
  }

  let decoded: string;
  try {
    decoded = atob(header.slice("Basic ".length));
  } catch {
    return unauthorized();
  }

  const colon = decoded.indexOf(":");
  if (colon === -1) {
    return unauthorized();
  }

  const providedUser = decoded.slice(0, colon);
  const providedPassword = decoded.slice(colon + 1);
  if (providedUser !== user || providedPassword !== password) {
    return unauthorized();
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Protect everything except Next internals and common static assets.
     * /api/health is allowed inside proxy() above.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
