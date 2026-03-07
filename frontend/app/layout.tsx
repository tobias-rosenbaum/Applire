import type { Metadata } from "next";

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
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#f5f5f5" }}>
        {children}
      </body>
    </html>
  );
}
