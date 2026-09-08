import { dump as dumpYaml } from "js-yaml";

import { GithubFileError } from "@/lib/github";
import type { ConfigEntry, ConfigPayload } from "@/lib/types";

const ALLOWED_KEYS = new Set(["riders", "horses", "nations"]);

function assertConfigEntry(entry: unknown, label: string, index: number): void {
  if (typeof entry === "string") {
    return;
  }
  if (entry === null || typeof entry !== "object" || Array.isArray(entry)) {
    throw new GithubFileError(
      `${label}[${index}] must be a string or object`,
      400,
    );
  }
  const obj = entry as Record<string, unknown>;
  for (const key of Object.keys(obj)) {
    if (key !== "name" && key !== "title" && key !== "active") {
      throw new GithubFileError(
        `${label}[${index}] has unknown field: ${key}`,
        400,
      );
    }
  }
  if ("name" in obj && obj.name !== undefined && typeof obj.name !== "string") {
    throw new GithubFileError(`${label}[${index}].name must be a string`, 400);
  }
  if (
    "title" in obj &&
    obj.title !== undefined &&
    typeof obj.title !== "string"
  ) {
    throw new GithubFileError(`${label}[${index}].title must be a string`, 400);
  }
  if (
    "active" in obj &&
    obj.active !== undefined &&
    obj.active !== null &&
    typeof obj.active !== "boolean"
  ) {
    throw new GithubFileError(
      `${label}[${index}].active must be a boolean`,
      400,
    );
  }
}

/** Structural validation for PUT /api/config (empty names / duplicates → H2). */
export function parseConfigBody(body: unknown): ConfigPayload {
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    throw new GithubFileError("Request body must be a JSON object", 400);
  }

  const raw = body as Record<string, unknown>;
  for (const key of Object.keys(raw)) {
    if (!ALLOWED_KEYS.has(key)) {
      throw new GithubFileError(`Unknown field: ${key}`, 400);
    }
  }

  const out: ConfigPayload = {};

  for (const key of ["riders", "horses"] as const) {
    if (!(key in raw)) {
      continue;
    }
    const value = raw[key];
    if (!Array.isArray(value)) {
      throw new GithubFileError(`${key} must be an array`, 400);
    }
    value.forEach((entry, index) => assertConfigEntry(entry, key, index));
    out[key] = value as ConfigEntry[];
  }

  if ("nations" in raw) {
    const value = raw.nations;
    if (!Array.isArray(value)) {
      throw new GithubFileError("nations must be an array", 400);
    }
    if (!value.every((item) => typeof item === "string")) {
      throw new GithubFileError("nations entries must be strings", 400);
    }
    out.nations = value;
  }

  return out;
}

export function configToYaml(config: ConfigPayload): string {
  const doc: Record<string, unknown> = {};
  if (config.riders !== undefined) {
    doc.riders = config.riders;
  }
  if (config.horses !== undefined) {
    doc.horses = config.horses;
  }
  if (config.nations !== undefined) {
    doc.nations = config.nations;
  }
  return dumpYaml(doc, {
    lineWidth: -1,
    noRefs: true,
    sortKeys: false,
  });
}
