import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg:       "var(--bg)",
        background: "var(--background)",
        surface:  "var(--surface)",
        surface2: "var(--surface2)",
        border:   "var(--border)",
        text:     "var(--text)",
        text2:    "var(--text2)",
        accent:   "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        node: {
          project:    "#6366F1",
          company:    "#F59E0B",
          contractor: "#10B981",
          person:     "#EC4899",
          consultant: "#8B5CF6",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        lg: "12px",
        xl: "16px",
      },
    },
  },
  plugins: [],
};
export default config;
