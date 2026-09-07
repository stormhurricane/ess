import { load as loadYaml } from "js-yaml";
import { NextResponse } from "next/server";

import { getRepoTextFile, GithubFileError, jsonError } from "@/lib/github";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const raw = await getRepoTextFile("config.yaml");
    let parsed: unknown;
    try {
      parsed = loadYaml(raw);
    } catch {
      throw new GithubFileError("Invalid YAML in config.yaml", 502);
    }
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new GithubFileError(
        "config.yaml must parse to a YAML mapping/object",
        502,
      );
    }
    return NextResponse.json(parsed);
  } catch (error) {
    return jsonError(error);
  }
}
