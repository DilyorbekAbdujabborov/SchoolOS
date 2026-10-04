/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        /* Semantic tokens. These read from CSS variables set in `index.css`,
         * which are redefined under `.dark` — so `bg-surface`, `border-line`
         * and `text-ink-muted` are theme-correct everywhere with no `dark:`
         * twin. Alpha modifiers (`bg-surface/60`) work because the variables
         * hold bare RGB channels.
         *
         * The four neutral steps carry the layout:
         *   canvas  — the page plane
         *   surface — cards, panels, tables
         *   raised  — insets and hovered rows
         *   sunken  — wells, tracks, disabled fills
         */
        canvas: "rgb(var(--c-canvas) / <alpha-value>)",
        surface: {
          DEFAULT: "rgb(var(--c-surface) / <alpha-value>)",
          raised: "rgb(var(--c-raised) / <alpha-value>)",
          sunken: "rgb(var(--c-sunken) / <alpha-value>)",
        },
        line: {
          DEFAULT: "rgb(var(--c-line) / <alpha-value>)",
          soft: "rgb(var(--c-line-soft) / <alpha-value>)",
          strong: "rgb(var(--c-line-strong) / <alpha-value>)",
        },
        ink: {
          DEFAULT: "rgb(var(--c-ink) / <alpha-value>)",
          muted: "rgb(var(--c-ink-muted) / <alpha-value>)",
          subtle: "rgb(var(--c-ink-subtle) / <alpha-value>)",
          inverse: "rgb(var(--c-ink-inverse) / <alpha-value>)",
        },

        // The app's single accent — Reef teal, the SchoolOS brand colour. Used
        // sparingly (primary actions, active nav, key stats), never as a
        // page-wide wash — see the brand book this palette implements.
        brand: {
          50: "#ecfdf9",
          100: "#d0f7ee",
          200: "#a6efdf",
          300: "#6fe3ce",
          400: "#2fd3bc",
          500: "#0eb39e",
          600: "#0a8f80",
          700: "#0c7267",
          800: "#0e5a52",
          900: "#114a44",
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
      fontFamily: {
        // A modern system stack: no webfont request, so the UI renders
        // identically offline and never flashes while a font loads.
        sans: [
          "Inter var",
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Noto Sans",
          "Arial",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },

      boxShadow: {
        // The app's only three depths — soft and neutral, never a blue glow.
        card: "var(--shadow-card)",
        raise: "var(--shadow-raise)",
        pop: "var(--shadow-pop)",
      },

      borderRadius: {
        // One radius ladder for the whole app, tuned slightly rounder than
        // Tailwind's defaults: 12px controls, 18px cards. Consistency here
        // does more for the "designed product" feel than any single colour.
        DEFAULT: "0.5rem",
        md: "0.625rem",
        lg: "0.75rem",
        xl: "0.875rem",
        "2xl": "1.125rem",
        "3xl": "1.5rem",
      },

      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
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
        spark: {
          "0%": { transform: "translate(0, 0) scale(1)", opacity: "1" },
          "100%": { transform: "translate(var(--sx), var(--sy)) scale(0.2)", opacity: "0" },
        },
        "enemy-bob": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6%)" },
        },
        "enemy-die": {
          "0%": { transform: "scale(1)", opacity: "1", filter: "brightness(2.5)" },
          "100%": { transform: "scale(0.3) rotate(25deg)", opacity: "0", filter: "brightness(3)" },
        },
        "lane-flow": {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "-80px 0" },
        },
        "lane-flow-y": {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "0 80px" },
        },
        "boss-enter": {
          "0%": { transform: "scale(0.4)", opacity: "0", filter: "brightness(3)" },
          "60%": { transform: "scale(1.15)", opacity: "1" },
          "100%": { transform: "scale(1)", opacity: "1", filter: "brightness(1)" },
        },
        "road-scroll": {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "0 160px" },
        },
        "scenery-scroll": {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "car-bob": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-2.5%)" },
        },
        "gate-rush": {
          "0%": { transform: "translate(-50%, 0) scale(0.08)", opacity: "0" },
          "20%": { opacity: "1" },
          "100%": { transform: "translate(-50%, 40%) scale(2.6)", opacity: "0" },
        },
        "speed-streak": {
          "0%": { opacity: "0", transform: "scale(0.7)" },
          "40%": { opacity: "0.9" },
          "100%": { opacity: "0", transform: "scale(1.5)" },
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
        shimmer: "shimmer 1.4s linear infinite",
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
        spark: "spark 0.6s ease-out forwards",
        "enemy-bob": "enemy-bob 2.2s ease-in-out infinite",
        "enemy-die": "enemy-die 0.7s ease-in forwards",
        "lane-flow": "lane-flow 1.6s linear infinite",
        "lane-flow-y": "lane-flow-y 1.6s linear infinite",
        "boss-enter": "boss-enter 1.1s cubic-bezier(0.22,1,0.36,1) both",
        "road-scroll": "road-scroll var(--road-speed, 0.6s) linear infinite",
        "scenery-scroll": "scenery-scroll var(--scenery-speed, 40s) linear infinite",
        "car-bob": "car-bob 0.9s ease-in-out infinite",
        "gate-rush": "gate-rush 1.1s ease-in forwards",
        "speed-streak": "speed-streak 0.7s ease-out infinite",
      },
    },
  },
  plugins: [],
};
