"use client";

import { useEffect, useState } from "react";

import type { ApiErrorBody } from "@/lib/types";

export type LoadState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ok"; data: T };

export function useJsonGet<T>(url: string): LoadState<T> {
  const [state, setState] = useState<LoadState<T>>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ status: "loading" });
      try {
        const res = await fetch(url, { cache: "no-store" });
        let body: (T & ApiErrorBody) | null = null;
        try {
          body = (await res.json()) as T & ApiErrorBody;
        } catch {
          throw new Error(
            res.ok
              ? "Antwort ist kein gültiges JSON"
              : `Fehler ${res.status}`,
          );
        }
        if (!res.ok) {
          throw new Error(body?.error || `Fehler ${res.status}`);
        }
        if (cancelled) return;
        setState({ status: "ok", data: body as T });
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
  }, [url]);

  return state;
}
