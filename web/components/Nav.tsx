"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Treffer" },
  { href: "/config", label: "Config" },
] as const;

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex w-full max-w-3xl items-center gap-8 px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight text-zinc-900">
          ESS
        </Link>
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
      </div>
    </header>
  );
}
