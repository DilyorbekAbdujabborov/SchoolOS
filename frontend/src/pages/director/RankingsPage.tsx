import { Leaderboard } from "../../components/Leaderboard";
import { PageHeader } from "../../components/PageHeader";

export function DirectorRankingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="XP va reyting" subtitle="Butun maktab bo'yicha o'quvchi va sinflar reytingi." />
      <Leaderboard />
    </div>
  );
}
