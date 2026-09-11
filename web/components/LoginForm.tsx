"use client";

import { useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { ErrorMessage } from "@/components/StatusMessage";
import {
  API_FETCH_INIT,
  friendlyApiError,
  friendlyCaughtError,
} from "@/lib/apiError";
import type { ApiErrorBody } from "@/lib/types";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/";

  const [user, setUser] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    try {
      const res = await fetch("/api/login", {
        ...API_FETCH_INIT,
        method: "POST",
        headers: {
          ...(API_FETCH_INIT.headers ?? {}),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user, password }),
      });
      let body: ApiErrorBody | null = null;
      try {
        body = (await res.json()) as ApiErrorBody;
      } catch {
        throw new Error(
          friendlyApiError(
            res.ok ? "Antwort ist kein gültiges JSON" : undefined,
            res.ok ? undefined : res.status,
          ),
        );
      }
      if (!res.ok) {
        if (res.status === 401) {
          throw new Error("Benutzer oder Passwort falsch.");
        }
        throw new Error(friendlyApiError(body?.error, res.status));
      }
      const target =
        nextPath.startsWith("/") && !nextPath.startsWith("//") ? nextPath : "/";
      router.replace(target);
      router.refresh();
    } catch (err) {
      setError(friendlyCaughtError(err, "Login fehlgeschlagen."));
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="mx-auto flex w-full max-w-sm flex-col gap-4"
    >
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-500">Benutzer</span>
        <input
          value={user}
          onChange={(e) => setUser(e.target.value)}
          autoComplete="username"
          required
          className="rounded border border-zinc-300 bg-white px-3 py-2 text-zinc-900 outline-none focus:border-zinc-500"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-zinc-500">Passwort</span>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
          className="rounded border border-zinc-300 bg-white px-3 py-2 text-zinc-900 outline-none focus:border-zinc-500"
        />
      </label>
      <button
        type="submit"
        disabled={pending}
        className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white enabled:hover:bg-zinc-800 disabled:opacity-40"
      >
        {pending ? "Anmelden …" : "Anmelden"}
      </button>
      {error ? <ErrorMessage>{error}</ErrorMessage> : null}
    </form>
  );
}
