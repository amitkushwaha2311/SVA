// LIFE//OS — Game Constants
// Single source of truth for all game mechanics

export const ATTRIBUTES = [
  'INTELLECT',
  'STRENGTH', 
  'DISCIPLINE',
  'CREATIVITY',
  'SOCIAL',
  'RECOVERY',
] as const;

export type Attribute = typeof ATTRIBUTES[number];

export const DIFFICULTIES = ['EASY', 'MEDIUM', 'HARD', 'EPIC'] as const;
export type Difficulty = typeof DIFFICULTIES[number];

// ─── XP Formula ──────────────────────────────────────────────────────────────
// requiredXP(level) = Math.floor(100 * level^1.7)
export function requiredXPForLevel(level: number): number {
  return Math.floor(100 * Math.pow(level, 1.7));
}

// ─── Difficulty XP Multipliers ───────────────────────────────────────────────
export const DIFFICULTY_XP: Record<string, number> = {
  EASY: 30,
  MEDIUM: 60,
  HARD: 120,
  EPIC: 250,
};

export const DIFFICULTY_GOLD: Record<string, number> = {
  EASY: 10,
  MEDIUM: 25,
  HARD: 60,
  EPIC: 150,
};

export const DIFFICULTY_ATTRIBUTE_GAIN: Record<string, number> = {
  EASY: 1,
  MEDIUM: 2,
  HARD: 3,
  EPIC: 5,
};

// ─── Combo Multipliers (streak-based) ────────────────────────────────────────
export function getComboMultiplier(streak: number): number {
  if (streak >= 30) return 1.5;
  if (streak >= 14) return 1.3;
  if (streak >= 7)  return 1.2;
  if (streak >= 3)  return 1.1;
  return 1.0;
}

// ─── Attribute → Quest Category Map ──────────────────────────────────────────
export const ATTRIBUTE_KEYWORDS: Record<Attribute, string[]> = {
  INTELLECT:  ['code', 'coding', 'read', 'study', 'learn', 'program', 'book', 'research', 'write', 'math'],
  STRENGTH:   ['gym', 'workout', 'run', 'exercise', 'lift', 'swim', 'sport', 'hike', 'walk', 'train'],
  DISCIPLINE: ['plan', 'schedule', 'wake', 'sleep', 'journal', 'habit', 'routine', 'organize', 'meditat'],
  CREATIVITY: ['draw', 'design', 'art', 'music', 'creat', 'paint', 'sketch', 'compose', 'build', 'craft'],
  SOCIAL:     ['meet', 'network', 'call', 'friend', 'team', 'collaborat', 'talk', 'social', 'event', 'help'],
  RECOVERY:   ['sleep', 'rest', 'recover', 'stretch', 'yoga', 'breath', 'nap', 'relax', 'meditat', 'spa'],
};

// ─── Streak Milestones ────────────────────────────────────────────────────────
export const STREAK_MILESTONES = [3, 7, 14, 30, 60, 100];

// ─── Archetypes ───────────────────────────────────────────────────────────────
export const ARCHETYPES = [
  {
    id: 'THE_BUILDER',
    name: 'THE BUILDER',
    description: 'You create systems, products, and solutions. Your strength is persistence and output.',
    icon: '🔨',
    primaryAttribute: 'DISCIPLINE' as Attribute,
    bonusAttributes: { DISCIPLINE: 5, INTELLECT: 3, CREATIVITY: 2 },
  },
  {
    id: 'THE_SCHOLAR',
    name: 'THE SCHOLAR',
    description: 'You seek knowledge and mastery. Learning is your superpower.',
    icon: '📚',
    primaryAttribute: 'INTELLECT' as Attribute,
    bonusAttributes: { INTELLECT: 5, DISCIPLINE: 3, CREATIVITY: 2 },
  },
  {
    id: 'THE_ATHLETE',
    name: 'THE ATHLETE',
    description: 'Physical mastery is your foundation. Your body is your tool.',
    icon: '⚡',
    primaryAttribute: 'STRENGTH' as Attribute,
    bonusAttributes: { STRENGTH: 5, DISCIPLINE: 3, RECOVERY: 2 },
  },
  {
    id: 'THE_CREATOR',
    name: 'THE CREATOR',
    description: 'You make things that didn\'t exist before. Ideas flow through you.',
    icon: '🎨',
    primaryAttribute: 'CREATIVITY' as Attribute,
    bonusAttributes: { CREATIVITY: 5, INTELLECT: 2, SOCIAL: 3 },
  },
  {
    id: 'THE_EXPLORER',
    name: 'THE EXPLORER',
    description: 'You seek new experiences, connections, and perspectives. Life is your map.',
    icon: '🧭',
    primaryAttribute: 'SOCIAL' as Attribute,
    bonusAttributes: { SOCIAL: 5, RECOVERY: 3, CREATIVITY: 2 },
  },
] as const;

// ─── Level-up Gold Bonus ──────────────────────────────────────────────────────
export const LEVEL_UP_GOLD_BONUS = 100;

// ─── Boss Damage by Attribute ─────────────────────────────────────────────────
export const BOSS_DAMAGE_BY_ATTRIBUTE: Record<string, number> = {
  INTELLECT:  80,
  STRENGTH:   100,
  DISCIPLINE: 70,
  CREATIVITY: 60,
  SOCIAL:     50,
  RECOVERY:   40,
};

// ─── Trait condition keys ─────────────────────────────────────────────────────
export const TRAIT_CONDITIONS = {
  DEEP_WORKER:      'deep_worker',
  RELENTLESS:       'relentless',
  ATHLETE:          'athlete',
  CREATOR:          'creator',
  GENERALIST:       'generalist',
  FAST_LEARNER:     'fast_learner',
  BALANCED:         'balanced',
  BUILDER:          'builder',
  NIGHT_OWL:        'night_owl',
  EARLY_RISER:      'early_riser',
  SOCIAL_BUTTERFLY: 'social_butterfly',
} as const;
