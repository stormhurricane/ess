import { jsonOk } from "@/lib/github";
import { SESSION_COOKIE } from "@/lib/session";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST() {
  const response = jsonOk({ ok: true });
  response.cookies.set(SESSION_COOKIE, "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return response;
}
