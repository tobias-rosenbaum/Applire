import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1B4F72",
        teal: "#2A8F9D",
        gold: "#C9A84C",
        success: "#2D9F6F",
        warning: "#E5A832",
        critical: "#D94F4F",
        neutral: {
          light: "#F5F7FA",
          dark: "#2C3E50",
        },
      },
      fontFamily: {
        heading: ["Poppins", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
      },
      borderRadius: {
        "lg": "12px",
      },
      boxShadow: {
        "soft": "0 2px 8px rgba(0,0,0,0.08)",
        "card": "0 4px 16px rgba(0,0,0,0.12)",
      },
    },
  },
  plugins: [],
};
export default config;