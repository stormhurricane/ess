"use client";

import { useEffect, useState } from "react";

import {
  ErrorMessage,
  LoadingMessage,
  SuccessMessage,
} from "@/components/StatusMessage";
import { friendlyApiError, friendlyCaughtError } from "@/lib/apiError";
import type {
  ApiErrorBody,
  ScrapeDispatchPayload,
  ScrapeRun,
  ScrapeStatusPayload,
} from "@/lib/types";

const POLL_MS = 10_000;
const RESULT_HINT = "Ergebnis in ca. 5–15 Min auf der Treffer-Seite.";

type PanelState =
  | { phase: "loading" }
  | { phase: "ready"; run: ScrapeRun | null }
  | { phase: "error"; message: string };

function isRunning(run: ScrapeRun | null): boolean {
  if (!run) return false;
  return run.status === "queued" || run.status === "in_progress" || run.status === "waiting" || run.status === "requested" || run.status === "pending";
}

function formatWhen(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("de-DE", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function statusLabel(run: ScrapeRun): string {
  if (run.status === "completed") {
    if (run.conclusion === "success") return "Erfolgreich";
    if (run.conclusion === "failure") return "Fehlgeschlagen";
    if (run.conclusion === "cancelled") return "Abgebrochen";
    return run.conclusion ? `Beendet (${run.conclusion})` : "Beendet";
  }
  if (run.status === "queued") return "In der Warteschlange";
  if (run.status === "in_progress") return "Läuft …";
  return run.status;
}

async function fetchStatus(): Promise<ScrapeStatusPayload> {
  const res = await fetch("/api/scrape/status", { cache: "no-store" });
  let body: (ScrapeStatusPayload & ApiErrorBody) | null = null;
  try {
    body = (await res.json()) as ScrapeStatusPayload & ApiErrorBody;
  } catch {
    throw new Error(
      friendlyApiError(
        res.ok ? "Antwort ist kein gültiges JSON" : undefined,
        res.ok ? undefined : res.status,
      ),
    );
  }
  if (!res.ok) {
    throw new Error(friendlyApiError(body?.error, res.status));
  }
  return body as ScrapeStatusPayload;
}

export function ScrapePanel() {
  const [panel, setPanel] = useState<PanelState>({ phase: "loading" });
  const [triggering, setTriggering] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionInfo, setActionInfo] = useState<string | null>(null);

  async function refresh() {
    try {
      const data = await fetchStatus();
      setPanel({ phase: "ready", run: data.run });
    } catch (error) {
      setPanel({
        phase: "error",
        message: friendlyCaughtError(
          error,
          "Status konnte nicht geladen werden.",
        ),
      });
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const run = panel.phase === "ready" ? panel.run : null;
  const running = isRunning(run);

  useEffect(() => {
    if (!running) return;
    const id = window.setInterval(() => {
      void refresh();
    }, POLL_MS);
    return () => window.clearInterval(id);
  }, [running, run?.id]);

  async function startScrape() {
    setTriggering(true);
    setActionError(null);
    setActionInfo(null);
    try {
      const res = await fetch("/api/scrape", {
        method: "POST",
        cache: "no-store",
      });
      let body: (ScrapeDispatchPayload & ApiErrorBody) | null = null;
      try {
        body = (await res.json()) as ScrapeDispatchPayload & ApiErrorBody;
      } catch {
        throw new Error(
          friendlyApiError(
            res.ok ? "Antwort ist kein gültiges JSON" : undefined,
            res.ok ? undefined : res.status,
          ),
        );
      }
      if (!res.ok) {
        throw new Error(friendlyApiError(body?.error, res.status));
      }
      setActionInfo(`Scrape gestartet. ${RESULT_HINT}`);
      await refresh();
    } catch (error) {
      setActionError(
        friendlyCaughtError(error, "Scrape konnte nicht gestartet werden."),
      );
    } finally {
      setTriggering(false);
    }
  }

  const busy = triggering || running;

  return (
    <section className="flex flex-col gap-3 border-b border-zinc-200 pb-6">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => void startScrape()}
          disabled={busy}
          className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white enabled:hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {triggering
            ? "Starte …"
            : running
              ? "Scrape läuft …"
              : "Jetzt scrapen"}
        </button>
        {busy ? (
          <span
            className="inline-block size-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-800"
            aria-hidden
          />
        ) : null}
      </div>
      <p className="text-sm text-zinc-500">{RESULT_HINT}</p>

      {panel.phase === "loading" ? (
        <LoadingMessage>Lade Scrape-Status …</LoadingMessage>
      ) : null}
      {panel.phase === "error" ? (
        <ErrorMessage>{panel.message}</ErrorMessage>
      ) : null}
      {panel.phase === "ready" && run ? (
        <p className="text-sm text-zinc-700">
          Letzter Lauf:{" "}
          <span className="font-medium text-zinc-900">{statusLabel(run)}</span>
          {" · "}
          {formatWhen(run.updated_at)}
          {" · "}
          <a
            href={run.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="underline decoration-zinc-300 underline-offset-2 hover:decoration-zinc-700"
          >
            Details
          </a>
        </p>
      ) : null}
      {panel.phase === "ready" && !run ? (
        <p className="text-sm text-zinc-600">Noch kein Scrape-Lauf bekannt.</p>
      ) : null}

      {actionInfo ? <SuccessMessage>{actionInfo}</SuccessMessage> : null}
      {actionError ? <ErrorMessage>{actionError}</ErrorMessage> : null}
    </section>
  );
}
