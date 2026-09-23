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
        "floor-drop": {
          "0%": { opacity: "0", transform: "translateY(-28px)" },
          "65%": { opacity: "1", transform: "translateY(2px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "floor-flash": {
          "0%": { opacity: "0.55" },
          "100%": { opacity: "0" },
        },
        "tower-glow": {
          "0%, 100%": { filter: "drop-shadow(0 0 0 rgba(96,165,250,0))" },
          "50%": { filter: "drop-shadow(0 0 14px rgba(96,165,250,0.55))" },
        },
        "float-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "20%": { opacity: "1", transform: "translateY(0)" },
          "80%": { opacity: "1", transform: "translateY(-6px)" },
          "100%": { opacity: "0", transform: "translateY(-12px)" },
        },
        "code-reveal": {
          "0%": { opacity: "0", transform: "rotateX(90deg) scale(0.9)" },
          "60%": { opacity: "1", transform: "rotateX(-12deg) scale(1.06)" },
          "100%": { opacity: "1", transform: "rotateX(0) scale(1)" },
        },
        "segment-glow": {
          "0%": { boxShadow: "0 0 0 0 rgba(59,130,246,0)" },
          "40%": { boxShadow: "0 0 26px 4px rgba(59,130,246,0.65)" },
          "100%": { boxShadow: "0 0 14px 0 rgba(59,130,246,0.3)" },
        },
        "alert-flash": {
          "0%": { boxShadow: "inset 0 0 0 2px rgba(239,68,68,0.9), 0 0 24px rgba(239,68,68,0.35)" },
          "100%": { boxShadow: "inset 0 0 0 2px rgba(239,68,68,0), 0 0 0 rgba(239,68,68,0)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(600%)" },
        },
        aura: {
          "0%": { transform: "scale(0.7)", opacity: "0.8" },
          "100%": { transform: "scale(2)", opacity: "0" },
        },
        "lid-open": {
          "0%": { transform: "translateY(0) rotate(0deg)" },
          "100%": { transform: "translateY(-30px) rotate(-16deg)" },
        },
        "rays-in": {
          "0%": { transform: "scale(0.4)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        "sparkle-rise": {
          "0%": { transform: "translateY(0)", opacity: "0" },
          "20%": { opacity: "1" },
          "100%": { transform: "translateY(-70px)", opacity: "0" },
        },
        "map-in": {
          "0%": { opacity: "0", transform: "scale(1.03)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fighter-idle": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-4px)" },
        },
        "fighter-attack": {
          "0%": { transform: "translateX(0)" },
          "25%": { transform: "translateX(-10px) scale(0.98)" },
          "50%": { transform: "translateX(36px) scale(1.04)" },
          "100%": { transform: "translateX(0)" },
        },
        "fighter-hit": {
          "0%": { transform: "translateX(0)", filter: "brightness(1)" },
          "20%": { transform: "translateX(-18px) rotate(-3deg)", filter: "brightness(1.9)" },
          "100%": { transform: "translateX(0)", filter: "brightness(1)" },
        },
        "fighter-victory": {
          "0%": { transform: "translateY(0) scale(1)" },
          "100%": { transform: "translateY(-10px) scale(1.06)" },
        },
        "fighter-defeat": {
          "0%": { transform: "translateY(0) rotate(0deg)", opacity: "1", filter: "grayscale(0)" },
          "100%": { transform: "translateY(10px) rotate(-7deg)", opacity: "0.55", filter: "grayscale(0.8)" },
        },
        "arm-strike": {
          "0%, 100%": { transform: "rotate(0deg)" },
          "45%": { transform: "rotate(-38deg) translateX(6px)" },
        },
        projectile: {
          "0%": { transform: "translate(0, 0) scale(0.4)", opacity: "0" },
          "15%": { opacity: "1" },
          "100%": { transform: "translate(var(--dx), var(--dy)) scale(1)", opacity: "1" },
        },
        impact: {
          "0%": { transform: "translate(-50%, -50%) scale(0.2)", opacity: "1" },
          "100%": { transform: "translate(-50%, -50%) scale(2.4)", opacity: "0" },
        },
        "shield-flash": {
          "0%": { opacity: "0", transform: "scale(0.85)" },
          "30%": { opacity: "1", transform: "scale(1)" },
          "100%": { opacity: "0", transform: "scale(1.08)" },
        },
        "combo-pop": {
          "0%": { transform: "scale(0.7)" },
          "60%": { transform: "scale(1.18)" },
          "100%": { transform: "scale(1)" },
        },
        "particle-rise": {
          "0%": { transform: "translateY(0)", opacity: "0" },
          "15%": { opacity: "0.8" },
          "100%": { transform: "translateY(-160px)", opacity: "0" },
        },
        "banner-in": {
          "0%": { opacity: "0", transform: "scale(1.4)", letterSpacing: "0.6em" },
          "100%": { opacity: "1", transform: "scale(1)", letterSpacing: "0.2em" },
        },
        shake: {
          "0%, 100%": { transform: "translateX(0)" },
          "20%": { transform: "translateX(-6px)" },
          "40%": { transform: "translateX(5px)" },
          "60%": { transform: "translateX(-3px)" },
          "80%": { transform: "translateX(2px)" },
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
        "floor-drop": "floor-drop 0.6s cubic-bezier(0.22,1,0.36,1) both",
        "floor-flash": "floor-flash 0.9s ease-out both",
        "tower-glow": "tower-glow 1.6s ease-in-out 2",
        "float-up": "float-up 1.4s ease-out both",
        shake: "shake 0.45s ease-in-out",
        "code-reveal": "code-reveal 0.55s cubic-bezier(0.22,1,0.36,1) both",
        "segment-glow": "segment-glow 1.1s ease-out both",
        "alert-flash": "alert-flash 0.9s ease-out both",
        scan: "scan 5s linear infinite",
        aura: "aura 2s ease-out infinite",
        "ring-once": "aura 1.1s ease-out 2",
        "lid-open": "lid-open 0.9s cubic-bezier(0.34,1.56,0.64,1) 0.35s both",
        "rays-in": "rays-in 1.2s ease-out 0.6s both",
        "sparkle-rise": "sparkle-rise 2.2s ease-out 0.9s infinite both",
        "map-in": "map-in 0.8s ease-out both",
        "fade-in": "fade-in 0.5s ease-out both",
        "fighter-idle": "fighter-idle 2.6s ease-in-out infinite",
        "fighter-attack": "fighter-attack 0.6s cubic-bezier(0.34,1.3,0.64,1)",
        "fighter-hit": "fighter-hit 0.5s ease-out",
        "fighter-victory": "fighter-victory 0.8s cubic-bezier(0.34,1.56,0.64,1) forwards",
        "fighter-defeat": "fighter-defeat 0.9s ease-out forwards",
        "arm-strike": "arm-strike 0.6s ease-out",
        projectile: "projectile 0.34s cubic-bezier(0.4,0,0.9,0.6) forwards",
        impact: "impact 0.55s ease-out forwards",
        "shield-flash": "shield-flash 0.6s ease-out forwards",
        "combo-pop": "combo-pop 0.4s cubic-bezier(0.34,1.56,0.64,1)",
        "particle-rise": "particle-rise 6s linear infinite",
        "banner-in": "banner-in 0.7s cubic-bezier(0.22,1,0.36,1) both",
      },
    },
  },
  plugins: [],
};
