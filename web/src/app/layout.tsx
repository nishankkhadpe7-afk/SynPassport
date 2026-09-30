import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SynPassport Assurance Dashboard",
  description: "Purpose-bound empirical assurance and Evidence Passports for synthetic datasets",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
