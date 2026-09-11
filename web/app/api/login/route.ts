import { NextResponse } from "next/server";

import { jsonError, jsonOk, GithubFileError } from "@/lib/github";
import {
  SESSION_COOKIE,
  createSessionToken,
  sessionCookieOptions,
} from "@/lib/session";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST(request: Request) {
  try {
    let body: unknown;
    try {
      body = await request.json();
    } catch {
      throw new GithubFileError("Request body must be valid JSON", 400);
    }
    if (body === null || typeof body !== "object" || Array.isArray(body)) {
      throw new GithubFileError("Request body must be a JSON object", 400);
    }
    const { user, password } = body as { user?: unknown; password?: unknown };
    if (typeof user !== "string" || typeof password !== "string") {
      throw new GithubFileError("user and password must be strings", 400);
    }

    const expectedUser = process.env.BASIC_AUTH_USER?.trim();
    const expectedPassword = process.env.BASIC_AUTH_PASSWORD?.trim();
    if (!expectedUser || !expectedPassword) {
      throw new GithubFileError("Basic auth is not configured", 500);
    }
    if (user !== expectedUser || password !== expectedPassword) {
      throw new GithubFileError("Invalid credentials", 401);
    }

    const token = await createSessionToken(expectedUser);
    const response = jsonOk({ ok: true });
    const secure = process.env.NODE_ENV === "production";
    response.cookies.set(
      SESSION_COOKIE,
      token,
      sessionCookieOptions(secure),
    );
    return response;
  } catch (error) {
    return jsonError(error);
  }
}
