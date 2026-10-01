import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0A0C0F",
        surface: {
          DEFAULT: "#11151A",
          dim: "#0A0C0F",
          bright: "#303A46",
          raised: "#171C23",
        },
        "surface-container": {
          lowest: "#050F19",
          low: "#11151A",
          DEFAULT: "#17202B",
          high: "#212B36",
          highest: "#2C3641",
        },
        border: {
          DEFAULT: "#232A33",
          subtle: "#1C232B",
        },
        outline: {
          DEFAULT: "#859490",
          variant: "#232A33",
        },
        primary: {
          DEFAULT: "#2DD4BF",
          bright: "#57F1DB",
          container: "#06B6D4",
          fixed: "#62FAE3",
          "fixed-dim": "#3CDDC7",
        },
        secondary: {
          DEFAULT: "#34D399",
          container: "#00A572",
          fixed: "#6FFBBE",
          "fixed-dim": "#4EDEA3",
        },
        tertiary: {
          DEFAULT: "#7BA7D9",
          container: "#39D69C",
          fixed: "#68FCBF",
          "fixed-dim": "#45DFA4",
        },
        error: {
          DEFAULT: "#F87171",
          container: "#93000A",
        },
        warning: {
          DEFAULT: "#F59E0B",
          container: "#78350F",
        },
        "on-surface": {
          DEFAULT: "#E6EAF0",
          variant: "#8B95A3",
          muted: "#566171",
        },
      },
      fontFamily: {
        sans: ["Inter", "Geist", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "Monaco", "monospace"],
      },
      borderRadius: {
        sm: "0.125rem",
        DEFAULT: "0.25rem",
        md: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
      },
      spacing: {
        gutter: "1.25rem",
        "gutter-lg": "1.5rem",
        "gutter-sm": "0.75rem",
        "space-xs": "0.25rem",
        "space-sm": "0.5rem",
        "space-md": "0.75rem",
        "space-lg": "1.25rem",
        "space-xl": "2rem",
      },
    },
  },
  plugins: [],
};
export default config;
