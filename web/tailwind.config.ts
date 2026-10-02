import type { Config } from "tailwindcss";

// All colours, radii and shadows resolve to the CSS variables in
// src/app/globals.css, so light and dark mode come from one token set.
const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        inverse: "var(--surface-inverse)",
        "on-inverse": "var(--on-inverse)",
        line: "var(--line)",
        "line-strong": "var(--line-strong)",
        ink: "var(--ink)",
        "ink-2": "var(--ink-2)",
        "ink-3": "var(--ink-3)",
        accent: "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        "accent-soft": "var(--accent-soft)",
        "on-accent": "var(--on-accent)",
        pass: "var(--pass)",
        "pass-soft": "var(--pass-soft)",
        warn: "var(--warn)",
        "warn-soft": "var(--warn-soft)",
        fail: "var(--fail)",
        "fail-soft": "var(--fail-soft)",
        neutral: "var(--neutral)",
        "neutral-soft": "var(--neutral-soft)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        display: ["var(--font-display)", "Georgia", "serif"],
        mono: ["var(--font-mono)"],
      },
      fontSize: {
        // Four sizes only: meta, body, section title, page title
        sm: ["13px", { lineHeight: "1.5" }],
        base: ["15px", { lineHeight: "1.55" }],
        lg: ["20px", { lineHeight: "1.35" }],
        xl: ["28px", { lineHeight: "1.2" }],
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        DEFAULT: "var(--radius)",
        lg: "var(--radius-lg)",
      },
      boxShadow: {
        DEFAULT: "var(--shadow)",
        overlay: "var(--shadow-overlay)",
      },
      transitionTimingFunction: {
        DEFAULT: "var(--ease)",
      },
      transitionDuration: {
        DEFAULT: "180ms",
      },
      maxWidth: {
        page: "1080px",
        prose: "68ch",
      },
    },
  },
  plugins: [],
};
export default config;
