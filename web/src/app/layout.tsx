import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SynPassport — Cockpit v2.4",
  description: "Purpose-bound empirical assurance and Evidence Passports for synthetic datasets",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#0a0c0f] text-[#e6eaf0] font-sans antialiased selection:bg-[#2dd4bf] selection:text-[#003731]">
        {children}
      </body>
    </html>
  );
}

