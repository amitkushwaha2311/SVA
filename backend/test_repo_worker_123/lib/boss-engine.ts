// LIFE//OS — Boss Engine
// Server-side boss damage calculation

import { BOSS_DAMAGE_BY_ATTRIBUTE } from './constants';

export interface BossDamageResult {
  bossId: string;
  damage: number;
  newHP: number;
  defeated: boolean;
}

export function calculateBossDamage(
  attribute: string,
  difficulty: string
): number {
  const baseByAttr = BOSS_DAMAGE_BY_ATTRIBUTE[attribute] ?? 50;
  const difficultyMult: Record<string, number> = {
    EASY:   0.75,
    MEDIUM: 1.0,
    HARD:   1.5,
    EPIC:   2.5,
  };
  const mult = difficultyMult[difficulty] ?? 1.0;
  return Math.floor(baseByAttr * mult);
}

export function applyBossDamage(
  currentHP: number,
  maxHP: number,
  damage: number
): { newHP: number; defeated: boolean } {
  const newHP = Math.max(0, currentHP - damage);
  return {
    newHP,
    defeated: newHP === 0,
  };
}
