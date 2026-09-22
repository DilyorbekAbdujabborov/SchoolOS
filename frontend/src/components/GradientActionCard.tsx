import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

type GradientTone = "brand" | "amber";

// A subtle same-hue lift, not a two-color wash — gradient is used sparingly,
// as one accent among plain cards, never as the page's default surface.
const TONE_CLASS: Record<GradientTone, string> = {
  brand: "from-brand-600 to-brand-700",
  amber: "from-amber-500 to-amber-600",
};

export function GradientActionCard({
  icon: Icon,
  title,
  subtitle,
  to,
  tone = "brand",
}: {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  to: string;
  tone?: GradientTone;
}) {
  return (
    <Link
      to={to}
      className={`flex items-center justify-between gap-4 rounded-2xl bg-gradient-to-br p-5 text-white transition-opacity hover:opacity-95 ${TONE_CLASS[tone]}`}
    >
      <div className="flex items-center gap-4">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/20">
          <Icon size={22} />
        </span>
        <div>
          <p className="font-semibold">{title}</p>
          <p className="text-sm text-white/80">{subtitle}</p>
        </div>
      </div>
      <ArrowRight size={20} className="shrink-0 text-white/80" />
    </Link>
  );
}
