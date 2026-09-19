export type Role = "DIRECTOR" | "TEACHER" | "STUDENT";

export interface CurrentUser {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: Role;
  must_change_password: boolean;
  total_xp: number | null;
  avatar_url: string | null;
}

export interface AttendanceCounts {
  present: number;
  late: number;
  absent: number;
  excused: number;
}

export interface LessonSummary {
  id: number;
  subject: string;
  school_class: string;
  start_time: string;
  end_time: string;
  room: string;
  topic: string;
  attendance_marked: boolean;
  is_own_lesson?: boolean;
}

export interface DirectorDashboard {
  total_students: number;
  total_teachers: number;
  total_classes: number;
  today_lessons: number;
  today_attendance: AttendanceCounts;
  total_tests: number;
  total_activities: number;
  total_xp_awarded: number;
  top_class: { name: string; total_xp: number } | null;
}

export interface TeacherDashboard {
  today_lessons: LessonSummary[];
  my_classes_count: number;
  unread_notifications: number;
}

export interface StudentDashboard {
  school_class: string | null;
  today_lessons: LessonSummary[];
  attendance_summary: AttendanceCounts & { total: number };
  unread_notifications: number;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Teacher {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  phone_number: string;
  bio: string;
}

export interface Student {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  school_class: number | null;
  school_class_name: string | null;
  birth_date: string | null;
  phone_number: string;
  parent_phone_number: string;
  total_xp: number;
}

export interface SchoolClass {
  id: number;
  name: string;
  class_teacher: number | null;
  class_teacher_name: string | null;
  students_count: number;
  total_xp: number;
  /** True when the requesting teacher leads this class (vs. just teaching a lesson in it). */
  is_my_homeroom: boolean;
}

export interface Subject {
  id: number;
  name: string;
}

export interface Lesson {
  id: number;
  subject: number;
  subject_name: string;
  school_class: number;
  school_class_name: string;
  teacher: number;
  teacher_name: string;
  date: string;
  start_time: string;
  end_time: string;
  room: string;
  topic: string;
}

export interface TimetableSlot {
  id: number;
  school_class: number;
  school_class_name: string;
  subject: number;
  subject_name: string;
  teacher: number;
  teacher_name: string;
  day_of_week: number;
  day_of_week_display: string;
  period_number: number;
  room: string;
}

export interface ClassAttendanceSummary {
  class_id: number;
  class_name: string;
  date: string;
  total_students: number;
  present: number;
  late: number;
  absent: number;
  excused: number;
  absent_students: RosterStudent[];
  late_students: RosterStudent[];
}

export type AttendanceStatus = "PRESENT" | "LATE" | "ABSENT" | "EXCUSED";

export interface AttendanceRecord {
  id: number;
  lesson: number;
  subject_name: string;
  school_class_name: string;
  lesson_date: string;
  student: number;
  student_name: string;
  status: AttendanceStatus;
  marked_by: number | null;
  marked_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface RosterStudent {
  id: number;
  full_name: string;
  email: string;
}

export interface NotificationItem {
  id: number;
  title: string;
  body: string;
  category: "GENERAL" | "ATTENDANCE";
  is_read: boolean;
  created_at: string;
}

export interface SchoolTimeConfig {
  start_time: string;
  end_time: string;
  period_duration_minutes: number;
  short_break_minutes: number;
  long_break_after_period: number;
  long_break_minutes: number;
}

export interface TelegramStatus {
  linked: boolean;
  telegram_username: string | null;
}

export interface TelegramLinkCode {
  code: string;
  expires_at: string;
  bot_username: string;
}

/** Same shape as `TelegramLinkCode` — a student generates this and shares it
 * with a parent, who types it into the bot to link their own Telegram chat. */
export type ParentLinkCode = TelegramLinkCode;

export interface ParentTelegramAccountItem {
  id: number;
  telegram_username: string;
  created_at: string;
}

export interface ParentContact {
  parent_phone_number: string;
}

// ---------- Learning: tests ----------

export interface TestOption {
  id: number;
  text: string;
}

export interface TestOptionWrite extends TestOption {
  question: number;
  is_correct: boolean;
}

export interface TestQuestion {
  id: number;
  text: string;
  order: number;
  options: TestOption[];
}

export interface TestQuestionWrite {
  id: number;
  test: number;
  text: string;
  order: number;
}

export interface TestSummary {
  id: number;
  title: string;
  subject: number;
  subject_name: string;
  school_class: number;
  school_class_name: string;
  teacher_name: string;
  time_limit_minutes: number | null;
  max_xp: number;
  is_published: boolean;
  question_count: number;
  /** Cap on question count for subjects that meet rarely (≤2x/week) in this class — null = no cap. */
  max_questions: number | null;
  created_at: string;
}

export interface TestDetail extends TestSummary {
  description: string;
  questions: TestQuestion[];
}

export type TestAttemptStatus = "IN_PROGRESS" | "SUBMITTED";

export interface TestAttempt {
  id: number;
  test: number;
  test_title: string;
  student: number;
  student_name: string;
  status: TestAttemptStatus;
  started_at: string;
  submitted_at: string | null;
  score_percent: number | null;
  xp_awarded: number | null;
  /** Present only on the `submit` response — set when the score was low enough
   * to auto-open an AI-assisted practice session (see `RemedialSession`). */
  remedial_session_id?: number | null;
}

// ---------- Learning: activities ----------

export type ActivityType = "ASSIGNMENT" | "CHALLENGE" | "TYPING" | "PRACTICAL" | "SPORTS";
export type ActivityStatus = "DRAFT" | "PUBLISHED" | "CLOSED";

export interface ActivitySummary {
  id: number;
  title: string;
  subject: number;
  subject_name: string;
  school_class: number;
  school_class_name: string;
  teacher_name: string;
  activity_type: ActivityType;
  max_xp: number;
  start_date: string | null;
  end_date: string | null;
  status: ActivityStatus;
  submission_count: number;
  created_at: string;
}

export interface ActivityDetail extends ActivitySummary {
  description: string;
}

export interface ActivityResult {
  score_percent: number;
  xp_awarded: number;
  feedback: string;
  graded_at: string;
}

export interface ActivitySubmission {
  id: number;
  activity: number;
  activity_title: string;
  student: number;
  student_name: string;
  content: string;
  attachment: string | null;
  submitted_at: string;
  result: ActivityResult | null;
}

// ---------- Gamification ----------

export type XpSource = "TEST" | "ACTIVITY";

export interface XPTransaction {
  id: number;
  student: number;
  student_name: string;
  amount: number;
  source: XpSource;
  reason: string;
  related_title: string | null;
  created_at: string;
}

export interface StudentLeaderboardEntry {
  rank: number;
  name: string;
  school_class_name: string | null;
  total_xp: number;
}

export interface ClassLeaderboardEntry {
  rank: number;
  name: string;
  total_xp: number;
}

export interface ClassGrowthPoint {
  date: string;
  total_xp: number;
}

export interface ClassGrowthSeries {
  class_id: number;
  class_name: string;
  points: ClassGrowthPoint[];
}

export interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlocked_at: string | null;
}

export type AchievementConditionType =
  | "FIRST_TEST"
  | "PERFECT_SCORE"
  | "XP_THRESHOLD"
  | "STREAK_LENGTH";

export interface AchievementManage {
  id: number;
  name: string;
  description: string;
  icon: string;
  condition_type: AchievementConditionType;
  condition_value: number;
  is_active: boolean;
}

export interface Streak {
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
}

export interface MyRank {
  rank: number;
  total_students: number;
  class_rank: number | null;
  total_classes: number;
}

// ---------- Director -> teacher tasks ----------

export type TeacherTaskCategory = "ADMINISTRATIVE" | "REPORT" | "MEETING" | "OTHER";

/** Director's view of a task they sent — how many teachers got it, how many are done. */
export interface TeacherTaskSummary {
  id: number;
  title: string;
  description: string;
  category: TeacherTaskCategory;
  category_display: string;
  is_broadcast: boolean;
  assignee_count: number;
  done_count: number;
  created_at: string;
}

/** A teacher's own copy of an assigned task. */
export interface TeacherTaskAssignment {
  id: number;
  task: number;
  title: string;
  description: string;
  category: TeacherTaskCategory;
  category_display: string;
  created_by_name: string;
  is_done: boolean;
  completed_at: string | null;
  created_at: string;
}

// ---------- Duels ----------

export type DuelStatus = "ACTIVE" | "COMPLETED";
export type DuelResult = "CHALLENGER" | "OPPONENT" | "DRAW" | null;
export type DuelRole = "challenger" | "opponent" | null;

/** Always framed from "my" side — `my_role`/`my_score_percent` etc. are
 * relative to whoever is asking, never the raw challenger/opponent fields. */
export interface DuelListItem {
  id: number;
  challenger: number;
  challenger_name: string;
  opponent: number;
  opponent_name: string;
  status: DuelStatus;
  result: DuelResult;
  my_role: DuelRole;
  my_score_percent: number | null;
  opponent_score_percent: number | null;
  i_won: boolean | null;
  i_have_submitted: boolean;
  opponent_has_submitted: boolean;
  created_at: string;
  completed_at: string | null;
}

export interface DuelQuestionItem {
  id: number;
  order: number;
  text: string;
  options: TestOption[];
}

export interface DuelRatingInfo {
  rating: number;
  tier: string;
  wins: number;
  losses: number;
  draws: number;
  total: number;
  win_rate: number;
  student_name?: string;
  school_class_name?: string | null;
}

// ---------- Remedial (AI tutor + practice game after a low test score) ----------

export type RemedialStatus = "PENDING" | "EXPLAINED" | "COMPLETED";

export interface RemedialSession {
  id: number;
  attempt: number;
  subject: number;
  subject_name: string;
  test_title: string;
  status: RemedialStatus;
  explanation: string;
  question_count: number;
  score_percent: number | null;
  xp_awarded: number | null;
  created_at: string;
  completed_at: string | null;
}

/** Answer-free, same principle as `TestQuestion` — no `correct_index` until after submit. */
export interface RemedialGameQuestion {
  text: string;
  options: string[];
}

// ---------- Games (self-serve "O'yinlar" section) ----------

export type GameType = "TUG_OF_WAR" | "QUIZ";
export type GameStatus = "ACTIVE" | "COMPLETED";

export interface GameSession {
  id: number;
  subject: number;
  subject_name: string;
  game_type: GameType;
  game_type_display: string;
  status: GameStatus;
  question_count: number;
  score_percent: number | null;
  xp_awarded: number | null;
  created_at: string;
  completed_at: string | null;
}

/** Answer-free, same shape as `RemedialGameQuestion`. */
export interface GameQuestion {
  text: string;
  options: string[];
}
