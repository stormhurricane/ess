import { jsonError, jsonOk } from "@/lib/github";
import { dispatchScrapeWorkflow } from "@/lib/workflow";

export const dynamic = "force-dynamic";
export const revalidate = 0;

/** Trigger scrape.yml via GitHub workflow_dispatch (I3). */
export async function POST() {
  try {
    const result = await dispatchScrapeWorkflow();
    return jsonOk(
      { ok: true, workflow: result.workflow, ref: result.ref },
      { status: 202 },
    );
  } catch (error) {
    return jsonError(error);
  }
}
