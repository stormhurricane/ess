import { NextResponse } from "next/server";

/**
 * Shared GitHub API errors for config/results/scrape routes:
 * - 400: invalid request body (PUT /api/config)
 * - 404: file or workflow missing
 * - 409: Contents API SHA conflict on update
 * - 500: required env missing or malformed (ESS_DATA_* / ESS_WORKFLOW_*)
 * - 502: GitHub upstream failure, or invalid YAML/JSON payload
 * Responses use JSON body `{ "error": string }`.
 */
export class GithubFileError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "GithubFileError";
  }
}

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new GithubFileError(`Missing environment variable ${name}`, 500);
  }
  return value;
}

function parseRepo(repo: string): { owner: string; name: string } {
  const parts = repo.split("/");
  if (parts.length !== 2 || !parts[0] || !parts[1]) {
    throw new GithubFileError(
      "ESS_DATA_REPO must be in the form owner/repo",
      500,
    );
  }
  return { owner: parts[0], name: parts[1] };
}

type GithubContentsFile = {
  encoding?: string;
  content?: string;
  type?: string;
  sha?: string;
};

function githubHeaders(token: string): HeadersInit {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "ess-web",
  };
}

async function getRepoFile(
  path: string,
): Promise<{ text: string; sha: string }> {
  const token = requireEnv("ESS_DATA_TOKEN");
  const { owner, name } = parseRepo(requireEnv("ESS_DATA_REPO"));
  const url = `https://api.github.com/repos/${owner}/${name}/contents/${path}`;

  const res = await fetch(url, {
    headers: githubHeaders(token),
    cache: "no-store",
  });

  if (res.status === 404) {
    throw new GithubFileError(`File not found: ${path}`, 404);
  }
  if (res.status === 401 || res.status === 403) {
    throw new GithubFileError("GitHub authentication or permission failed", 502);
  }
  if (!res.ok) {
    throw new GithubFileError(
      `GitHub Contents API error (${res.status})`,
      502,
    );
  }

  const body = (await res.json()) as GithubContentsFile;

  if (
    body.type !== "file" ||
    typeof body.content !== "string" ||
    typeof body.sha !== "string" ||
    !body.sha
  ) {
    throw new GithubFileError(`Unexpected GitHub response for ${path}`, 502);
  }

  const encoding = body.encoding ?? "base64";
  if (encoding !== "base64") {
    throw new GithubFileError(
      `Unsupported GitHub content encoding: ${encoding}`,
      502,
    );
  }

  const text = Buffer.from(body.content.replace(/\n/g, ""), "base64").toString(
    "utf-8",
  );
  return { text, sha: body.sha };
}

/** Fetch a text file from the private ess-data repo via GitHub Contents API. */
export async function getRepoTextFile(path: string): Promise<string> {
  const { text } = await getRepoFile(path);
  return text;
}

/** Update an existing text file in ess-data (fetches current blob SHA first). */
export async function putRepoTextFile(
  path: string,
  text: string,
  message: string,
): Promise<void> {
  const token = requireEnv("ESS_DATA_TOKEN");
  const { owner, name } = parseRepo(requireEnv("ESS_DATA_REPO"));
  const { sha } = await getRepoFile(path);
  const url = `https://api.github.com/repos/${owner}/${name}/contents/${path}`;

  const res = await fetch(url, {
    method: "PUT",
    headers: {
      ...githubHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      content: Buffer.from(text, "utf-8").toString("base64"),
      sha,
    }),
    cache: "no-store",
  });

  if (res.status === 409) {
    throw new GithubFileError(
      `Conflict updating ${path}: file changed (SHA mismatch)`,
      409,
    );
  }
  if (res.status === 401 || res.status === 403) {
    throw new GithubFileError("GitHub authentication or permission failed", 502);
  }
  if (!res.ok) {
    throw new GithubFileError(
      `GitHub Contents API update error (${res.status})`,
      502,
    );
  }
}

/** Prevent CDN/browser from serving empty 304s for authed API GETs. */
export const NO_STORE_HEADERS = {
  "Cache-Control": "private, no-store, no-cache, must-revalidate",
  Pragma: "no-cache",
  Expires: "0",
  Vary: "Authorization",
} as const;

export function jsonOk(data: unknown, init?: { status?: number }): NextResponse {
  return NextResponse.json(data, {
    status: init?.status ?? 200,
    headers: NO_STORE_HEADERS,
  });
}

export function jsonError(error: unknown): NextResponse {
  if (error instanceof GithubFileError) {
    return NextResponse.json(
      { error: error.message },
      { status: error.status, headers: NO_STORE_HEADERS },
    );
  }
  const message =
    error instanceof Error ? error.message : "Unexpected server error";
  return NextResponse.json(
    { error: message },
    { status: 500, headers: NO_STORE_HEADERS },
  );
}
