import { Suspense } from "react";

import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold tracking-tight">Anmelden</h1>
      <p className="text-sm text-zinc-600">
        ESS ist geschützt. Bitte mit Benutzer und Passwort anmelden.
      </p>
      <Suspense fallback={<p className="text-zinc-600">Lade …</p>}>
        <LoginForm />
      </Suspense>
    </main>
  );
}
