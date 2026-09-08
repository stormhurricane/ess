export function LoadingMessage({ children }: { children: string }) {
  return <p className="text-zinc-600">{children}</p>;
}

export function ErrorMessage({ children }: { children: string }) {
  return (
    <p
      className="rounded border border-red-200 bg-red-50 px-3 py-2 text-red-800"
      role="alert"
    >
      {children}
    </p>
  );
}

export function SuccessMessage({ children }: { children: string }) {
  return (
    <p
      className="rounded border border-emerald-200 bg-emerald-50 px-3 py-2 text-emerald-900"
      role="status"
    >
      {children}
    </p>
  );
}

export function EmptyMessage({ children }: { children: string }) {
  return <p className="text-zinc-600">{children}</p>;
}
