import { load as loadYaml } from "js-yaml";

import { configCommitMessage, configToYaml, parseConfigBody } from "@/lib/config";
import {
  getRepoTextFile,
  GithubFileError,
  jsonError,
  jsonOk,
  putRepoTextFile,
} from "@/lib/github";

export const dynamic = "force-dynamic";
export const revalidate = 0;

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
    return jsonOk(parsed);
  } catch (error) {
    return jsonError(error);
  }
}

export async function PUT(request: Request) {
  try {
    let body: unknown;
    try {
      body = await request.json();
    } catch {
      throw new GithubFileError("Request body must be valid JSON", 400);
    }

    const config = parseConfigBody(body);
    const yaml = configToYaml(config);
    await putRepoTextFile("config.yaml", yaml, configCommitMessage(config));
    return jsonOk(config);
  } catch (error) {
    return jsonError(error);
  }
}
