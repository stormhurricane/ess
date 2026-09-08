"use client";

import { useEffect, useState } from "react";

import type { ApiErrorBody, Hit, ResultsPayload } from "@/lib/types";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ok"; data: ResultsPayload };

function HitList({ hits }: { hits: Hit[] }) {
  return (
    <ul className="mt-1 space-y-1 text-sm text-zinc-700">
      {hits.map((hit, index) => {
        const label = [hit.location, hit.date].filter(Boolean).join(" · ");
        const key = `${hit.url ?? ""}-${hit.location ?? ""}-${hit.date ?? ""}-${index}`;
        if (hit.url) {
          return (
            <li key={key}>
              <a
                href={hit.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-900 underline decoration-zinc-300 underline-offset-2 hover:decoration-zinc-700"
              >
                {label || hit.url}
              </a>
            </li>
          );
        }
        return <li key={key}>{label || "Ohne Details"}</li>;
      })}
    </ul>
  );
}

function NameGroup({
  title,
  entries,
}: {
  title: string;
  entries: Record<string, Hit[]>;
}) {
  const names = Object.keys(entries).sort((a, b) => a.localeCompare(b, "de"));
  if (names.length === 0) {
    return null;
  }

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
        {title}
      </h2>
      <ul className="space-y-4">
        {names.map((name) => (
          <li key={name}>
            <div className="font-medium text-zinc-900">{name}</div>
            <HitList hits={entries[name] ?? []} />
          </li>
        ))}
      </ul>
    </section>
  );
}

export function TrefferList() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ status: "loading" });
      try {
        const res = await fetch("/api/results", { cache: "no-store" });
        const body = (await res.json()) as ResultsPayload & ApiErrorBody;
        if (!res.ok) {
          throw new Error(body.error || `Fehler ${res.status}`);
        }
        if (cancelled) return;
        setState({ status: "ok", data: body });
      } catch (error) {
        if (cancelled) return;
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "Unbekannter Fehler",
        });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") {
    return <p className="text-zinc-600">Lade Treffer …</p>;
  }

  if (state.status === "error") {
    return (
      <p className="text-red-700" role="alert">
        {state.message}
      </p>
    );
  }

  const riders = state.data.gefundene_reiter ?? {};
  const horses = state.data.gefundene_pferde ?? {};
  const empty =
    Object.keys(riders).length === 0 && Object.keys(horses).length === 0;

  if (empty) {
    return <p className="text-zinc-600">Keine Treffer gefunden.</p>;
  }

  return (
    <div className="flex flex-col gap-10">
      <NameGroup title="Reiter" entries={riders} />
      <NameGroup title="Pferde" entries={horses} />
    </div>
  );
}
