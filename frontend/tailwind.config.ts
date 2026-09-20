import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f2f6ff",
          100: "#e3ebff",
          500: "#3355ff",
          600: "#2643db",
          900: "#101a3d",
        },
      },
    },
  },
  plugins: [],
};

export default config;
