import { NextResponse } from "next/server";

import { getRepoTextFile, GithubFileError, jsonError } from "@/lib/github";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const raw = await getRepoTextFile("result.json");
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      throw new GithubFileError("Invalid JSON in result.json", 502);
    }
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new GithubFileError(
        "result.json must parse to a JSON object",
        502,
      );
    }
    return NextResponse.json(parsed);
  } catch (error) {
    return jsonError(error);
  }
}
