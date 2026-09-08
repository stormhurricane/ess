import { ConfigView } from "@/components/ConfigView";

export default function ConfigPage() {
  return (
    <main className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold tracking-tight">Config</h1>
      <ConfigView />
    </main>
  );
}
