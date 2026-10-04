// LIFE//OS — Core Game Engine
// Server-side only. All progression calculations happen here.

import {
  requiredXPForLevel,
  DIFFICULTY_XP,
  DIFFICULTY_GOLD,
  DIFFICULTY_ATTRIBUTE_GAIN,
  getComboMultiplier,
  STREAK_MILESTONES,
  LEVEL_UP_GOLD_BONUS,
  Attribute,
} from './constants';

export { getComboMultiplier };

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CharacterState {
  level: number;
  xp: number;
  xpToNextLevel: number;
  gold: number;
  intellect: number;
  strength: number;
  discipline: number;
  creativity: number;
  social: number;
  recovery: number;
  currentStreak: number;
  longestStreak: number;
  lastActiveDate: string | null;
  comboMultiplier: number;
}

export interface QuestRewards {
  xpBase: number;
  goldBase: number;
  xpFinal: number;
  goldFinal: number;
  comboUsed: number;
  attributeGain: number;
  attribute: string;
}

export interface LevelUpResult {
  levelsGained: number;
  newLevel: number;
  goldBonus: number;
}

export interface StreakResult {
  newStreak: number;
  longestStreak: number;
  streakBroken: boolean;
  milestoneReached: number | null;
}

export interface ProgressionResult {
  rewards: QuestRewards;
  streakResult: StreakResult;
  levelUpResult: LevelUpResult;
  newCharacter: CharacterState;
}

// ─── XP Calculation ──────────────────────────────────────────────────────────

export function calculateQuestRewards(
  difficulty: string,
  attribute: string,
  comboMultiplier: number
): QuestRewards {
  const xpBase = DIFFICULTY_XP[difficulty] ?? 30;
  const goldBase = DIFFICULTY_GOLD[difficulty] ?? 10;
  const attributeGain = DIFFICULTY_ATTRIBUTE_GAIN[difficulty] ?? 1;

  const xpFinal = Math.floor(xpBase * comboMultiplier);
  const goldFinal = Math.floor(goldBase * comboMultiplier);

  return {
    xpBase,
    goldBase,
    xpFinal,
    goldFinal,
    comboUsed: comboMultiplier,
    attributeGain,
    attribute,
  };
}

// ─── Level-up Processing ──────────────────────────────────────────────────────

export function processLevelUps(
  currentLevel: number,
  currentXP: number,
  xpGained: number
): { newLevel: number; newXP: number; xpToNextLevel: number; levelsGained: number; goldBonus: number } {
  let level = currentLevel;
  let xp = currentXP + xpGained;
  let levelsGained = 0;
  let goldBonus = 0;

  // Handle multiple level-ups correctly
  while (xp >= requiredXPForLevel(level)) {
    xp -= requiredXPForLevel(level);
    level++;
    levelsGained++;
    goldBonus += LEVEL_UP_GOLD_BONUS;
  }

  return {
    newLevel: level,
    newXP: xp,
    xpToNextLevel: requiredXPForLevel(level),
    levelsGained,
    goldBonus,
  };
}

// ─── Streak Calculation ───────────────────────────────────────────────────────

export function calculateStreak(
  currentStreak: number,
  longestStreak: number,
  lastActiveDate: string | null,
  today: string // YYYY-MM-DD
): StreakResult {
  let newStreak = currentStreak;
  let streakBroken = false;

  if (!lastActiveDate) {
    // First ever completion
    newStreak = 1;
  } else if (lastActiveDate === today) {
    // Already active today — no change
    newStreak = currentStreak;
  } else {
    // Check if yesterday
    const last = new Date(lastActiveDate);
    const todayDate = new Date(today);
    const diffMs = todayDate.getTime() - last.getTime();
    const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      // Consecutive day
      newStreak = currentStreak + 1;
    } else {
      // Streak broken
      newStreak = 1;
      streakBroken = true;
    }
  }

  const newLongest = Math.max(longestStreak, newStreak);

  // Check milestone
  const milestoneReached = STREAK_MILESTONES.find(
    (m) => newStreak === m && newStreak !== currentStreak
  ) ?? null;

  return {
    newStreak,
    longestStreak: newLongest,
    streakBroken,
    milestoneReached,
  };
}

// ─── Full Progression ─────────────────────────────────────────────────────────

export function processQuestCompletion(
  character: CharacterState,
  difficulty: string,
  attribute: string,
  today: string // YYYY-MM-DD
): ProgressionResult {
  const combo = character.comboMultiplier;
  const rewards = calculateQuestRewards(difficulty, attribute, combo);

  // Streak
  const streakResult = calculateStreak(
    character.currentStreak,
    character.longestStreak,
    character.lastActiveDate,
    today
  );

  // Level ups
  const levelUpResult = processLevelUps(
    character.level,
    character.xp,
    rewards.xpFinal
  );

  // Build new character state
  const newChar: CharacterState = { ...character };

  // Update XP and level
  newChar.xp = levelUpResult.newXP;
  newChar.level = levelUpResult.newLevel;
  newChar.xpToNextLevel = levelUpResult.xpToNextLevel;

  // Update gold
  newChar.gold = character.gold + rewards.goldFinal + levelUpResult.goldBonus;

  // Update attribute
  const attrKey = attribute.toLowerCase() as keyof CharacterState;
  if (typeof newChar[attrKey] === 'number') {
    (newChar[attrKey] as number) += rewards.attributeGain;
  }

  // Update streak
  newChar.currentStreak = streakResult.newStreak;
  newChar.longestStreak = streakResult.longestStreak;
  newChar.lastActiveDate = today;
  newChar.comboMultiplier = getComboMultiplier(streakResult.newStreak);

  return {
    rewards,
    streakResult,
    levelUpResult: {
      levelsGained: levelUpResult.levelsGained,
      newLevel: levelUpResult.newLevel,
      goldBonus: levelUpResult.goldBonus,
    },
    newCharacter: newChar,
  };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

export function getTodayString(): string {
  return new Date().toISOString().split('T')[0];
}

export function getXPProgress(xp: number, level: number): number {
  const required = requiredXPForLevel(level);
  return Math.min(100, Math.floor((xp / required) * 100));
}
