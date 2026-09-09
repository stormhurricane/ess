import { GithubFileError } from "@/lib/github";

const WORKFLOW_FILE = "scrape.yml";

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new GithubFileError(`Missing environment variable ${name}`, 500);
  }
  return value;
}

function parseRepo(
  repo: string,
  envName: string,
): { owner: string; name: string } {
  const parts = repo.split("/");
  if (parts.length !== 2 || !parts[0] || !parts[1]) {
    throw new GithubFileError(
      `${envName} must be in the form owner/repo`,
      500,
    );
  }
  return { owner: parts[0], name: parts[1] };
}

function workflowRepo(): { owner: string; name: string } {
  const explicit = process.env.ESS_WORKFLOW_REPO?.trim();
  if (explicit) {
    return parseRepo(explicit, "ESS_WORKFLOW_REPO");
  }
  // Same owner as ess-data, code/workflows live in sibling repo "ess".
  const { owner } = parseRepo(requireEnv("ESS_DATA_REPO"), "ESS_DATA_REPO");
  return { owner, name: "ess" };
}

function githubHeaders(token: string): HeadersInit {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "ess-web",
    "Content-Type": "application/json",
  };
}

/**
 * POST workflow_dispatch for scrape.yml on the code repo (ess).
 * Uses ESS_WORKFLOW_TOKEN; optional ESS_WORKFLOW_REPO / ESS_WORKFLOW_REF.
 */
export async function dispatchScrapeWorkflow(): Promise<{
  workflow: string;
  ref: string;
}> {
  const token = requireEnv("ESS_WORKFLOW_TOKEN");
  const { owner, name } = workflowRepo();
  const ref = process.env.ESS_WORKFLOW_REF?.trim() || "main";
  const url = `https://api.github.com/repos/${owner}/${name}/actions/workflows/${WORKFLOW_FILE}/dispatches`;

  const res = await fetch(url, {
    method: "POST",
    headers: githubHeaders(token),
    body: JSON.stringify({ ref }),
    cache: "no-store",
  });

  if (res.status === 401 || res.status === 403) {
    throw new GithubFileError("GitHub authentication or permission failed", 502);
  }
  if (res.status === 404) {
    throw new GithubFileError(
      `Workflow ${WORKFLOW_FILE} not found in ${owner}/${name} (ref ${ref})`,
      404,
    );
  }
  if (res.status !== 204 && res.status !== 200) {
    throw new GithubFileError(
      `GitHub workflow_dispatch error (${res.status})`,
      502,
    );
  }

  return { workflow: WORKFLOW_FILE, ref };
}
