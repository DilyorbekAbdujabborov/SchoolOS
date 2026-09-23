/** Sound-ready game events. The project has no audio yet, so games only
 * announce what happened; a future sound layer (or anything else — haptics,
 * analytics) subscribes once instead of every game growing its own hooks:
 *
 *   window.addEventListener(GAME_EVENT, (e) => play((e as CustomEvent<GameEventDetail>).detail.name));
 *
 * Nothing here ever autoplays anything. */

export const GAME_EVENT = "edugames:event";

export type GameEventName =
  | "correct"
  | "wrong"
  | "tower_attack"
  | "enemy_hit"
  | "enemy_defeated"
  | "base_hit"
  | "combo_up"
  | "power_boost"
  | "overcharge"
  | "wave_start"
  | "boss_arrival"
  | "victory"
  | "defeat"
  | "countdown"
  | "race_start"
  | "nitro"
  | "checkpoint"
  | "final_lap"
  | "finish";

export interface GameEventDetail {
  name: GameEventName;
  game: string;
}

export function emitGameEvent(game: string, name: GameEventName) {
  window.dispatchEvent(new CustomEvent<GameEventDetail>(GAME_EVENT, { detail: { name, game } }));
}
