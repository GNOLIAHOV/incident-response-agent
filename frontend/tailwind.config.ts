import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas: "#080B11",
        surface: {
          950: "#080B11",
          900: "#0D121D",
          850: "#121927",
          800: "#182235",
          700: "#222F49",
        },
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "SF Mono",
          "Fira Code",
          "Consolas",
          "ui-monospace",
          "monospace",
        ],
      },
      borderColor: {
        hairline: "rgba(255, 255, 255, 0.07)",
        strong: "rgba(255, 255, 255, 0.14)",
      },
    },
  },
  plugins: [],
};

export default config;
