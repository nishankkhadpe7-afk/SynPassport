import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Display serif (Source Serif 4, SIL Open Font License) used only for the wordmark.
// Bundled in the repo so builds never depend on an internet connection.
const display = localFont({
  src: [{ path: "../fonts/source-serif-4-latin-500-normal.woff2", weight: "500", style: "normal" }],
  variable: "--font-display",
  display: "swap",
  fallback: ["Georgia", "serif"],
});

export const metadata: Metadata = {
  title: "SynPassport",
  description: "Purpose-bound assurance and Evidence Passports for synthetic datasets",
};

// Applies a saved theme before first paint so the page never flashes the wrong theme.
const themeScript = `try{var t=localStorage.getItem('synpassport-theme');if(t==='dark'||t==='light'){document.documentElement.setAttribute('data-theme',t);}}catch(e){}`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={display.variable}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-bg text-ink antialiased">{children}</body>
    </html>
  );
}
