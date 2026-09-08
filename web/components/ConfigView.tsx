"use client";

import { useEffect, useState } from "react";

import type { ApiErrorBody, ConfigEntry, ConfigPayload } from "@/lib/types";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ok"; data: ConfigPayload };

function entryDisplay(entry: ConfigEntry): { name: string; active: boolean } {
  if (typeof entry === "string") {
    return { name: entry.trim() || "(ohne Namen)", active: true };
  }
  const name = String(entry.name || entry.title || "").trim() || "(ohne Namen)";
  const active = entry.active === undefined || entry.active === null ? true : Boolean(entry.active);
  return { name, active };
}

function EntryList({
  title,
  entries,
}: {
  title: string;
  entries: ConfigEntry[];
}) {
  if (entries.length === 0) {
    return (
      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          {title}
        </h2>
        <p className="text-sm text-zinc-600">Keine Einträge.</p>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
        {title}
      </h2>
      <ul className="space-y-2">
        {entries.map((entry, index) => {
          const { name, active } = entryDisplay(entry);
          return (
            <li
              key={`${name}-${index}`}
              className="flex items-baseline justify-between gap-4 text-sm"
            >
              <span className="font-medium text-zinc-900">{name}</span>
              <span className={active ? "text-zinc-600" : "text-zinc-400"}>
                {active ? "aktiv" : "inaktiv"}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function ConfigView() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ status: "loading" });
      try {
        const res = await fetch("/api/config", { cache: "no-store" });
        const body = (await res.json()) as ConfigPayload & ApiErrorBody;
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
    return <p className="text-zinc-600">Lade Config …</p>;
  }

  if (state.status === "error") {
    return (
      <p className="text-red-700" role="alert">
        {state.message}
      </p>
    );
  }

  const riders = state.data.riders ?? [];
  const horses = state.data.horses ?? [];
  const nations = state.data.nations ?? [];

  return (
    <div className="flex flex-col gap-10">
      <EntryList title="Reiter" entries={riders} />
      <EntryList title="Pferde" entries={horses} />
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          Nationen
        </h2>
        {nations.length === 0 ? (
          <p className="text-sm text-zinc-600">Keine Nationen (Default im Scraper: GER).</p>
        ) : (
          <ul className="flex flex-wrap gap-2 text-sm">
            {nations.map((code) => (
              <li
                key={code}
                className="rounded border border-zinc-200 bg-white px-2 py-1 font-medium text-zinc-900"
              >
                {code}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
