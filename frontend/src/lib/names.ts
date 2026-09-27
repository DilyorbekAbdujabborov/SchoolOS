import type { CurrentUser } from "../types";

/** Login → ism ko'rinishi: "abduraxmonov.j" → "Abduraxmonov J.", "director" → "Director". */
export function nameFromUsername(username?: string | null): string {
  const local = (username || "").split("@")[0]?.trim();
  const parts = (local || "").split(/[._\-\s]+/).filter(Boolean);
  if (!parts.length) return username || "";
  const surname = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
  if (parts.length > 1) {
    const initial = parts[parts.length - 1].charAt(0).toUpperCase();
    return `${surname} ${initial}.`;
  }
  return surname;
}

/** Qisqa ism: "Familiya + ism bosh harfi" (masalan "Abdusalimov S."). Xom login hech qachon chiqmaydi. */
export function shortName(user: CurrentUser | null | undefined): string {
  if (!user) return "";
  const first = (user.first_name || "").trim();
  const last = (user.last_name || "").trim();
  if (first && last) return `${last} ${first.charAt(0).toUpperCase()}.`;
  if (first) return first;
  return nameFromUsername(user.username);
}

/** To'liq ism: "Ism Familiya" (masalan "Sirojiddin Abdusalimov"). Xom login hech qachon chiqmaydi. */
export function fullName(user: CurrentUser | null | undefined): string {
  if (!user) return "";
  const first = (user.first_name || "").trim();
  const last = (user.last_name || "").trim();
  if (first || last) return `${first} ${last}`.trim();
  return nameFromUsername(user.username);
}

/** Rolga qarab: o'quvchiga to'liq ism, ustoz/direktorga "Familiya + bosh harf". */
export function publicName(user: CurrentUser | null | undefined): string {
  if (!user) return "";
  return user.role === "STUDENT" ? fullName(user) : shortName(user);
}