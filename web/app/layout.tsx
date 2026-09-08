import type { Metadata } from "next";

import { Nav } from "@/components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "ESS",
  description: "Equi-Score Scraper — private web UI",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="de" className="h-full antialiased">
      <body className="flex min-h-full flex-col font-sans">
        <Nav />
        <div className="mx-auto w-full max-w-3xl flex-1 px-6 py-8">{children}</div>
      </body>
    </html>
  );
}
