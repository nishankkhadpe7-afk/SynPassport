import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        state: {
          pass: {
            DEFAULT: "#10b981",
            bg: "rgba(16, 185, 129, 0.12)",
            border: "rgba(16, 185, 129, 0.35)",
            text: "#34d399",
          },
          warning: {
            DEFAULT: "#f59e0b",
            bg: "rgba(245, 158, 11, 0.12)",
            border: "rgba(245, 158, 11, 0.35)",
            text: "#fbbf24",
          },
          fail: {
            DEFAULT: "#ef4444",
            bg: "rgba(239, 68, 68, 0.12)",
            border: "rgba(239, 68, 68, 0.35)",
            text: "#f87171",
          },
          insufficient: {
            DEFAULT: "#64748b",
            bg: "rgba(100, 116, 139, 0.15)",
            border: "rgba(148, 163, 184, 0.35)",
            text: "#94a3b8",
          },
        },
      },
    },
  },
  plugins: [],
};
export default config;
