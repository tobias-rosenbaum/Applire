import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: "Apliqa — DACH CV Tailoring",
  description: "AI-powered Lebenslauf tailoring for the DACH market",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body className="font-body bg-neutral-light text-neutral-dark antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}