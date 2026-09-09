import { NextResponse } from "next/server";

import { jsonError } from "@/lib/github";
import { getLatestScrapeRun } from "@/lib/workflow";

export const dynamic = "force-dynamic";

/** Latest scrape.yml run: status + timestamps (I4). */
export async function GET() {
  try {
    const result = await getLatestScrapeRun();
    return NextResponse.json(result);
  } catch (error) {
    return jsonError(error);
  }
}
