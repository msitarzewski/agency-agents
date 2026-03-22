import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        primary: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
          950: "#022c22",
        },
        secondary: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f",
          950: "#451a03",
        },
        accent: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
          950: "#082f49",
        },
        "health-red": {
          DEFAULT: "#ef4444",
          light: "#fca5a5",
          dark: "#b91c1c",
        },
        "edu-blue": {
          DEFAULT: "#3b82f6",
          light: "#93c5fd",
          dark: "#1d4ed8",
        },
        "env-green": {
          DEFAULT: "#22c55e",
          light: "#86efac",
          dark: "#15803d",
        },
        "water-cyan": {
          DEFAULT: "#06b6d4",
          light: "#67e8f9",
          dark: "#0e7490",
        },
        "hunger-orange": {
          DEFAULT: "#f97316",
          light: "#fdba74",
          dark: "#c2410c",
        },
      },
      animation: {
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "count-up": "countUp 1s ease-out",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": {
            opacity: "1",
            filter: "brightness(1)",
          },
          "50%": {
            opacity: "0.8",
            filter: "brightness(1.2)",
          },
        },
        countUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
