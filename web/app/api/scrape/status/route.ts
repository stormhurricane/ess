import { jsonError, jsonOk } from "@/lib/github";
import { getLatestScrapeRun } from "@/lib/workflow";

export const dynamic = "force-dynamic";
export const revalidate = 0;

/** Latest scrape.yml run: status + timestamps (I4). */
export async function GET() {
  try {
    const result = await getLatestScrapeRun();
    return jsonOk(result);
  } catch (error) {
    return jsonError(error);
  }
}
