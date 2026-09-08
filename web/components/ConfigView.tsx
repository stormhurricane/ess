"use client";

import {
  EmptyMessage,
  ErrorMessage,
  LoadingMessage,
} from "@/components/StatusMessage";
import { useJsonGet } from "@/lib/useJsonGet";
import type { ConfigEntry, ConfigPayload } from "@/lib/types";

function entryDisplay(entry: ConfigEntry): { name: string; active: boolean } {
  if (typeof entry === "string") {
    return { name: entry.trim() || "(ohne Namen)", active: true };
  }
  const name = String(entry.name || entry.title || "").trim() || "(ohne Namen)";
  const active =
    entry.active === undefined || entry.active === null
      ? true
      : Boolean(entry.active);
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
        <EmptyMessage>Keine Einträge.</EmptyMessage>
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
  const state = useJsonGet<ConfigPayload>("/api/config");

  if (state.status === "loading") {
    return <LoadingMessage>Lade Config …</LoadingMessage>;
  }

  if (state.status === "error") {
    return <ErrorMessage>{state.message}</ErrorMessage>;
  }

  const riders = state.data.riders ?? [];
  const horses = state.data.horses ?? [];
  const nations = (state.data.nations ?? []).map(String);

  return (
    <div className="flex flex-col gap-10">
      <EntryList title="Reiter" entries={riders} />
      <EntryList title="Pferde" entries={horses} />
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          Nationen
        </h2>
        {nations.length === 0 ? (
          <EmptyMessage>
            Keine Nationen gesetzt (Scraper-Default: GER).
          </EmptyMessage>
        ) : (
          <ul className="flex flex-wrap gap-2 text-sm">
            {nations.map((code, index) => (
              <li
                key={`${code}-${index}`}
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
