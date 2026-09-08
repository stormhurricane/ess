import { dump as dumpYaml } from "js-yaml";

import { GithubFileError } from "@/lib/github";
import type { ConfigEntry, ConfigPayload } from "@/lib/types";

const ALLOWED_KEYS = new Set(["riders", "horses", "nations"]);

/** Display name from string or {name|title}; empty/whitespace → null (like CLI). */
function entryName(entry: ConfigEntry): string | null {
  if (typeof entry === "string") {
    const name = entry.trim();
    return name || null;
  }
  const name = String(entry.name || entry.title || "").trim();
  return name || null;
}

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

function assertNamedEntries(entries: ConfigEntry[], label: string): void {
  const seen = new Set<string>();
  entries.forEach((entry, index) => {
    const name = entryName(entry);
    if (!name) {
      throw new GithubFileError(`${label}[${index}] name must not be empty`, 400);
    }
    if (seen.has(name)) {
      throw new GithubFileError(
        `${label} contains duplicate name: ${name}`,
        400,
      );
    }
    seen.add(name);
  });
}

function assertNations(nations: string[]): void {
  const seen = new Set<string>();
  nations.forEach((raw, index) => {
    const code = raw.trim();
    if (!code) {
      throw new GithubFileError(`nations[${index}] must not be empty`, 400);
    }
    if (seen.has(code)) {
      throw new GithubFileError(`nations contains duplicate: ${code}`, 400);
    }
    seen.add(code);
  });
}

/** Validate PUT /api/config body (structure + empty names / duplicates). */
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
    const entries = value as ConfigEntry[];
    assertNamedEntries(entries, key);
    out[key] = entries;
  }

  if ("nations" in raw) {
    const value = raw.nations;
    if (!Array.isArray(value)) {
      throw new GithubFileError("nations must be an array", 400);
    }
    if (!value.every((item) => typeof item === "string")) {
      throw new GithubFileError("nations entries must be strings", 400);
    }
    assertNations(value);
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
