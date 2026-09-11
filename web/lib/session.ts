/** HttpOnly session cookie for GUI auth (iOS-friendly; Basic Auth remains optional). */

export const SESSION_COOKIE = "ess_session";
export const SESSION_MAX_AGE_SEC = 60 * 60 * 24 * 30; // 30 days

function authSecret(): string {
  const secret =
    process.env.AUTH_SECRET?.trim() || process.env.BASIC_AUTH_PASSWORD?.trim();
  if (!secret) {
    throw new Error("Missing AUTH_SECRET or BASIC_AUTH_PASSWORD");
  }
  return secret;
}

function bytesToBase64Url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]!);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function hmacSign(secret: string, data: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(data),
  );
  return bytesToBase64Url(sig);
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let out = 0;
  for (let i = 0; i < a.length; i++) {
    out |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return out === 0;
}

/** Create signed session token: `exp.user.sig`. */
export async function createSessionToken(username: string): Promise<string> {
  const exp = String(Math.floor(Date.now() / 1000) + SESSION_MAX_AGE_SEC);
  const user = username.trim();
  const payload = `ess:${exp}:${user}`;
  const sig = await hmacSign(authSecret(), payload);
  return `${exp}.${user}.${sig}`;
}

export async function verifySessionToken(
  token: string,
  expectedUser: string,
): Promise<boolean> {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return false;
    const [expRaw, user, sig] = parts;
    if (!expRaw || !user || !sig) return false;
    if (user !== expectedUser.trim()) return false;
    const exp = Number(expRaw);
    if (!Number.isFinite(exp) || exp * 1000 < Date.now()) return false;
    const expected = await hmacSign(authSecret(), `ess:${expRaw}:${user}`);
    return timingSafeEqual(sig, expected);
  } catch {
    return false;
  }
}

export function sessionCookieOptions(secure: boolean) {
  return {
    httpOnly: true,
    secure,
    sameSite: "lax" as const,
    path: "/",
    maxAge: SESSION_MAX_AGE_SEC,
  };
}
