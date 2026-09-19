/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Matched to edu.sanbax.uz's own palette (sampled from its live computed
        // styles: primary button/active-nav #6f57cf, its CTA gradient
        // #8b5cf6→#6c3ce0, and the light-mode active-nav tint #ece8fb/#5b46b8).
        brand: {
          50: "#f3f1fc",
          100: "#ece8fb",
          200: "#d9d2f7",
          300: "#bcaeef",
          400: "#a38ee6",
          500: "#8b5cf6",
          600: "#6f57cf",
          700: "#5b46b8",
          800: "#4a3894",
          900: "#392a70",
        },
        // Sanbax's neutral surface — a violet-tinted near-black/near-white, not
        // Tailwind's default blue-gray slate. Overriding `slate` itself (rather
        // than adding a new family) reskins every existing bg-slate-*/text-slate-*/
        // border-slate-* usage across the app in one place. Dark-mode stops
        // (900/950) are sampled from sanbax's real card/page backgrounds
        // (#1c1a23/#17161d); light-mode stops (50) from its page background
        // (#f5f6fa); 100–800 are interpolated to keep a smooth, coherent ramp.
        slate: {
          50: "#f5f6fa",
          100: "#ececf3",
          200: "#dedce8",
          300: "#c3c0d1",
          400: "#9a98a6",
          500: "#82869a",
          600: "#6b6879",
          700: "#4a4757",
          800: "#2e2b36",
          900: "#1c1a23",
          950: "#17161d",
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
