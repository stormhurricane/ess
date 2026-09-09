import { ScrapePanel } from "@/components/ScrapePanel";
import { TrefferList } from "@/components/TrefferList";

export default function TrefferPage() {
  return (
    <main className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold tracking-tight">Treffer</h1>
      <ScrapePanel />
      <TrefferList />
    </main>
  );
}
