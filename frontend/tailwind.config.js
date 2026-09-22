/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // The app's single accent — a clean, vivid blue. Used sparingly (primary
        // actions, active nav, key stats), never as a page-wide wash — see the
        // design-system brief this palette implements.
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        // A true cool neutral (not blue- or violet-tinted) — overriding `slate`
        // itself reskins every existing bg-slate-*/text-slate-*/border-slate-*
        // usage across the app in one place. Dark and light are tuned as two
        // separate, deliberate surfaces rather than a mechanical inversion:
        // dark has three distinct steps (950 page → 900 card → 800 border) so
        // cards read as a lifted surface against a genuinely near-black page;
        // light stays a soft off-white (50) with plain white cards, so borders
        // stay optional rather than doing all the separation work.
        slate: {
          50: "#f7f8fa",
          100: "#eef0f3",
          200: "#e1e4ea",
          300: "#c7ccd6",
          400: "#98a0b3",
          500: "#6b7280",
          600: "#4b5262",
          700: "#343b4a",
          800: "#1c212c",
          900: "#141821",
          950: "#08090d",
        },
      },
      keyframes: {
        "pop-in": {
          "0%": { opacity: "0", transform: "scale(0.85) translateY(4px)" },
          "60%": { opacity: "1", transform: "scale(1.04) translateY(0)" },
          "100%": { opacity: "1", transform: "scale(1) translateY(0)" },
        },
        wave: {
          "0%, 60%, 100%": { transform: "rotate(0deg)" },
          "10%": { transform: "rotate(14deg)" },
          "20%": { transform: "rotate(-8deg)" },
          "30%": { transform: "rotate(14deg)" },
          "40%": { transform: "rotate(-4deg)" },
          "50%": { transform: "rotate(10deg)" },
        },
      },
      animation: {
        "pop-in": "pop-in 0.4s cubic-bezier(0.34,1.56,0.64,1) both",
        wave: "wave 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
