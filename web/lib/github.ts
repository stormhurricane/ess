import { NextResponse } from "next/server";

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

/** Fetch a text file from the private ess-data repo via GitHub Contents API. */
export async function getRepoTextFile(path: string): Promise<string> {
  const token = requireEnv("ESS_DATA_TOKEN");
  const { owner, name } = parseRepo(requireEnv("ESS_DATA_REPO"));
  const url = `https://api.github.com/repos/${owner}/${name}/contents/${path}`;

  const res = await fetch(url, {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "ess-web",
    },
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

  const body = (await res.json()) as {
    encoding?: string;
    content?: string;
    type?: string;
  };

  if (body.type !== "file" || typeof body.content !== "string") {
    throw new GithubFileError(`Unexpected GitHub response for ${path}`, 502);
  }

  const encoding = body.encoding ?? "base64";
  if (encoding !== "base64") {
    throw new GithubFileError(
      `Unsupported GitHub content encoding: ${encoding}`,
      502,
    );
  }

  return Buffer.from(body.content.replace(/\n/g, ""), "base64").toString(
    "utf-8",
  );
}

export function jsonError(error: unknown): NextResponse {
  if (error instanceof GithubFileError) {
    return NextResponse.json({ error: error.message }, { status: error.status });
  }
  const message =
    error instanceof Error ? error.message : "Unexpected server error";
  return NextResponse.json({ error: message }, { status: 500 });
}
