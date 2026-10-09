/**
 * Client-config capabilities — what the platform owner allows this organization.
 *
 * The backend sends only the *denied* keys (`<resource>.<action>`) on `/auth/me/`
 * and refuses those requests with 403 `capability_denied`. This module mirrors
 * that so the UI never shows what the API would refuse: denying
 * `<resource>.read` closes the whole section (sidebar item + route).
 */
import type { CurrentUser } from "../types";

export type CapabilityAction = "read" | "create" | "update" | "delete";

/** `/app/<role>/<segment>` → backend resource. Pages not listed are never gated. */
const SEGMENT_RESOURCE: Record<string, string> = {
  students: "students",
  teachers: "teachers",
  classes: "classes",
  class: "classes",
  subjects: "subjects",
  lessons: "timetable",
  timetable: "timetable",
  attendance: "attendance",
  materials: "materials",
  tests: "tests",
  activities: "activities",
  tasks: "tasks",
  games: "games",
  "question-pools": "games",
  duels: "duels",
  rankings: "gamification",
  xp: "gamification",
  achievements: "gamification",
  league: "gamification",
  leaderboard: "gamification",
  streak: "gamification",
  reports: "reports",
};

/** The resource an in-app path belongs to, or null when it is never gated. */
export function resourceForAppPath(path: string): string | null {
  // ["", "app", "<role>", "<segment>", ...]
  const segment = path.split("/")[3];
  return (segment && SEGMENT_RESOURCE[segment]) || null;
}

export function can(
  user: CurrentUser | null | undefined,
  key: string,
): boolean {
  const denied = user?.capabilities?.denied ?? [];
  const [resource] = key.split(".");
  return !denied.includes(key) && !denied.includes(`${resource}.read`);
}

/** Whether the user may open the in-app page at `path`. */
export function canOpen(
  user: CurrentUser | null | undefined,
  path: string,
): boolean {
  const resource = resourceForAppPath(path);
  return resource === null || can(user, `${resource}.read`);
}
