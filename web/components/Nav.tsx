"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { API_FETCH_INIT } from "@/lib/apiError";

const links = [
  { href: "/", label: "Treffer" },
  { href: "/config", label: "Config" },
] as const;

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const onLogin = pathname === "/login";

  async function logout() {
    try {
      await fetch("/api/logout", { ...API_FETCH_INIT, method: "POST" });
    } catch {
      // still leave the UI
    }
    router.replace("/login");
    router.refresh();
  }

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex w-full max-w-3xl items-center gap-8 px-6 py-4">
        <Link
          href={onLogin ? "/login" : "/"}
          className="text-lg font-semibold tracking-tight text-zinc-900"
        >
          ESS
        </Link>
        {!onLogin ? (
          <>
            <nav className="flex gap-4 text-sm">
              {links.map(({ href, label }) => {
                const active =
                  href === "/"
                    ? pathname === "/"
                    : pathname === href || pathname.startsWith(`${href}/`);
                return (
                  <Link
                    key={href}
                    href={href}
                    className={
                      active
                        ? "font-medium text-zinc-900"
                        : "text-zinc-500 hover:text-zinc-800"
                    }
                  >
                    {label}
                  </Link>
                );
              })}
            </nav>
            <button
              type="button"
              onClick={() => void logout()}
              className="ml-auto text-sm text-zinc-500 hover:text-zinc-800"
            >
              Abmelden
            </button>
          </>
        ) : null}
      </div>
    </header>
  );
}
