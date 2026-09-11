"use client";

import { useState, type FormEvent } from "react";

import {
  EmptyMessage,
  ErrorMessage,
  LoadingMessage,
  SuccessMessage,
} from "@/components/StatusMessage";
import { useJsonGet } from "@/lib/useJsonGet";
import { friendlyApiError, friendlyCaughtError } from "@/lib/apiError";
import type { ApiErrorBody, ConfigEntry, ConfigPayload } from "@/lib/types";

type NamedEntry = { name: string; active: boolean };

type Draft = {
  riders: NamedEntry[];
  horses: NamedEntry[];
  nations: string[];
};

type SaveState =
  | { status: "idle" }
  | { status: "saving" }
  | { status: "success"; message: string }
  | { status: "error"; message: string };

function normalizeEntry(entry: ConfigEntry): NamedEntry {
  if (typeof entry === "string") {
    return { name: entry.trim(), active: true };
  }
  const name = String(entry.name || entry.title || "").trim();
  const active =
    entry.active === undefined || entry.active === null
      ? true
      : Boolean(entry.active);
  return { name, active };
}

function normalizePayload(data: ConfigPayload): Draft {
  return {
    riders: (data.riders ?? []).map(normalizeEntry),
    horses: (data.horses ?? []).map(normalizeEntry),
    nations: (data.nations ?? []).map((code) => String(code).trim()).filter(Boolean),
  };
}

function draftEqual(a: Draft, b: Draft): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

function toPayload(draft: Draft): ConfigPayload {
  return {
    riders: draft.riders.map(({ name, active }) => ({ name, active })),
    horses: draft.horses.map(({ name, active }) => ({ name, active })),
    nations: draft.nations,
  };
}

function EntrySection({
  title,
  entries,
  onToggle,
  onRemove,
  onAdd,
}: {
  title: string;
  entries: NamedEntry[];
  onToggle: (index: number) => void;
  onRemove: (index: number) => void;
  onAdd: (name: string) => string | null;
}) {
  const [name, setName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  function submit(e: FormEvent) {
    e.preventDefault();
    const error = onAdd(name);
    if (error) {
      setLocalError(error);
      return;
    }
    setName("");
    setLocalError(null);
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-medium uppercase tracking-wide text-zinc-500">
        {title}
      </h2>
      {entries.length === 0 ? (
        <EmptyMessage>Keine Einträge.</EmptyMessage>
      ) : (
        <ul className="space-y-2">
          {entries.map((entry, index) => (
            <li
              key={`${entry.name}-${index}`}
              className="flex flex-wrap items-center gap-3 text-sm"
            >
              <span className="min-w-0 flex-1 font-medium text-zinc-900">
                {entry.name}
              </span>
              <label className="flex cursor-pointer items-center gap-2 text-zinc-600">
                <input
                  type="checkbox"
                  checked={entry.active}
                  onChange={() => onToggle(index)}
                  className="size-4 accent-zinc-800"
                />
                aktiv
              </label>
              <button
                type="button"
                onClick={() => onRemove(index)}
                className="text-zinc-500 underline-offset-2 hover:text-zinc-900 hover:underline"
              >
                Löschen
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={submit} className="flex flex-wrap items-end gap-2">
        <label className="flex min-w-[12rem] flex-1 flex-col gap-1 text-sm">
          <span className="text-zinc-500">Neuer Eintrag</span>
          <input
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              if (localError) setLocalError(null);
            }}
            className="rounded border border-zinc-300 bg-white px-2 py-1.5 text-zinc-900 outline-none focus:border-zinc-500"
            autoComplete="off"
          />
        </label>
        <button
          type="submit"
          className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 hover:bg-zinc-50"
        >
          Hinzufügen
        </button>
      </form>
      {localError ? <ErrorMessage>{localError}</ErrorMessage> : null}
    </section>
  );
}

function NationsSection({
  nations,
  onRemove,
  onAdd,
}: {
  nations: string[];
  onRemove: (index: number) => void;
  onAdd: (code: string) => string | null;
}) {
  const [code, setCode] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  function submit(e: FormEvent) {
    e.preventDefault();
    const error = onAdd(code);
    if (error) {
      setLocalError(error);
      return;
    }
    setCode("");
    setLocalError(null);
  }

  return (
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
          {nations.map((item, index) => (
            <li
              key={`${item}-${index}`}
              className="flex items-center gap-2 rounded border border-zinc-200 bg-white px-2 py-1 font-medium text-zinc-900"
            >
              {item}
              <button
                type="button"
                onClick={() => onRemove(index)}
                className="text-zinc-400 hover:text-zinc-800"
                aria-label={`${item} entfernen`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={submit} className="flex flex-wrap items-end gap-2">
        <label className="flex min-w-[8rem] flex-col gap-1 text-sm">
          <span className="text-zinc-500">Code (z. B. GER)</span>
          <input
            value={code}
            onChange={(e) => {
              setCode(e.target.value);
              if (localError) setLocalError(null);
            }}
            className="rounded border border-zinc-300 bg-white px-2 py-1.5 uppercase text-zinc-900 outline-none focus:border-zinc-500"
            autoComplete="off"
          />
        </label>
        <button
          type="submit"
          className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 hover:bg-zinc-50"
        >
          Hinzufügen
        </button>
      </form>
      {localError ? <ErrorMessage>{localError}</ErrorMessage> : null}
    </section>
  );
}

function ConfigEditor({ initial }: { initial: Draft }) {
  const [draft, setDraft] = useState<Draft>(initial);
  const [saved, setSaved] = useState<Draft>(initial);
  const [saveState, setSaveState] = useState<SaveState>({ status: "idle" });
  const dirty = !draftEqual(draft, saved);

  function addNamed(
    key: "riders" | "horses",
    rawName: string,
  ): string | null {
    const name = rawName.trim();
    if (!name) {
      return "Name darf nicht leer sein.";
    }
    if (draft[key].some((entry) => entry.name === name)) {
      return `„${name}“ ist bereits eingetragen.`;
    }
    setDraft((prev) => ({
      ...prev,
      [key]: [...prev[key], { name, active: true }],
    }));
    setSaveState({ status: "idle" });
    return null;
  }

  async function save() {
    setSaveState({ status: "saving" });
    try {
      const res = await fetch("/api/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toPayload(draft)),
        cache: "no-store",
      });
      let body: (ConfigPayload & ApiErrorBody) | null = null;
      try {
        body = (await res.json()) as ConfigPayload & ApiErrorBody;
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
      const next = normalizePayload(body ?? toPayload(draft));
      setDraft(next);
      setSaved(next);
      setSaveState({ status: "success", message: "Config gespeichert." });
    } catch (error) {
      setSaveState({
        status: "error",
        message: friendlyCaughtError(error, "Speichern fehlgeschlagen."),
      });
    }
  }

  return (
    <div className="flex flex-col gap-10">
      <EntrySection
        title="Reiter"
        entries={draft.riders}
        onToggle={(index) => {
          setDraft((prev) => ({
            ...prev,
            riders: prev.riders.map((entry, i) =>
              i === index ? { ...entry, active: !entry.active } : entry,
            ),
          }));
          setSaveState({ status: "idle" });
        }}
        onRemove={(index) => {
          setDraft((prev) => ({
            ...prev,
            riders: prev.riders.filter((_, i) => i !== index),
          }));
          setSaveState({ status: "idle" });
        }}
        onAdd={(name) => addNamed("riders", name)}
      />
      <EntrySection
        title="Pferde"
        entries={draft.horses}
        onToggle={(index) => {
          setDraft((prev) => ({
            ...prev,
            horses: prev.horses.map((entry, i) =>
              i === index ? { ...entry, active: !entry.active } : entry,
            ),
          }));
          setSaveState({ status: "idle" });
        }}
        onRemove={(index) => {
          setDraft((prev) => ({
            ...prev,
            horses: prev.horses.filter((_, i) => i !== index),
          }));
          setSaveState({ status: "idle" });
        }}
        onAdd={(name) => addNamed("horses", name)}
      />
      <NationsSection
        nations={draft.nations}
        onRemove={(index) => {
          setDraft((prev) => ({
            ...prev,
            nations: prev.nations.filter((_, i) => i !== index),
          }));
          setSaveState({ status: "idle" });
        }}
        onAdd={(raw) => {
          const code = raw.trim().toUpperCase();
          if (!code) {
            return "Code darf nicht leer sein.";
          }
          if (draft.nations.includes(code)) {
            return `„${code}“ ist bereits eingetragen.`;
          }
          setDraft((prev) => ({
            ...prev,
            nations: [...prev.nations, code],
          }));
          setSaveState({ status: "idle" });
          return null;
        }}
      />

      <div className="flex flex-col gap-3 border-t border-zinc-200 pt-6">
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => void save()}
            disabled={!dirty || saveState.status === "saving"}
            className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white enabled:hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {saveState.status === "saving" ? "Speichern …" : "Speichern"}
          </button>
          {dirty ? (
            <span className="text-sm text-zinc-500">Ungespeicherte Änderungen</span>
          ) : null}
        </div>
        {saveState.status === "success" ? (
          <SuccessMessage>{saveState.message}</SuccessMessage>
        ) : null}
        {saveState.status === "error" ? (
          <ErrorMessage>{saveState.message}</ErrorMessage>
        ) : null}
      </div>
    </div>
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

  return <ConfigEditor initial={normalizePayload(state.data)} />;
}
