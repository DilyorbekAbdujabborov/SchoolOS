import { Leaderboard } from "../../components/Leaderboard";
import { PageHeader } from "../../components/PageHeader";

export function StudentLeaderboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Reyting" />
      <Leaderboard />
    </div>
  );
}
