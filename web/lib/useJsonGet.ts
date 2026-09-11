"use client";

import { useEffect, useState } from "react";

import {
  API_FETCH_INIT,
  friendlyApiError,
  friendlyCaughtError,
} from "@/lib/apiError";
import type { ApiErrorBody } from "@/lib/types";

export type LoadState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ok"; data: T };

const FETCH_TIMEOUT_MS = 20_000;

export function useJsonGet<T>(url: string): LoadState<T> {
  const [state, setState] = useState<LoadState<T>>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ status: "loading" });
      const controller = new AbortController();
      const timer = window.setTimeout(
        () => controller.abort(),
        FETCH_TIMEOUT_MS,
      );
      try {
        const res = await fetch(url, {
          ...API_FETCH_INIT,
          signal: controller.signal,
        });
        if (res.status === 304) {
          throw new Error(friendlyApiError(undefined, 304));
        }
        if (res.status === 401) {
          window.location.assign("/login");
          return;
        }
        let body: (T & ApiErrorBody) | null = null;
        try {
          body = (await res.json()) as T & ApiErrorBody;
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
        if (cancelled) return;
        setState({ status: "ok", data: body as T });
      } catch (error) {
        if (cancelled) return;
        if (error instanceof DOMException && error.name === "AbortError") {
          setState({
            status: "error",
            message:
              "Zeitüberschreitung — auf dem iPhone oft Login nötig. Seite neu laden oder /login öffnen.",
          });
          return;
        }
        setState({
          status: "error",
          message: friendlyCaughtError(error),
        });
      } finally {
        window.clearTimeout(timer);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [url]);

  return state;
}
