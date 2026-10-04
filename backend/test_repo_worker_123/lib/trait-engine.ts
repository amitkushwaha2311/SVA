// LIFE//OS — Trait Engine
// Evaluates behavioral patterns to unlock traits automatically

import { PrismaClient } from '@prisma/client';
import { TRAIT_CONDITIONS } from './constants';

// ─── Trait Evaluation ─────────────────────────────────────────────────────────

interface TraitContext {
  userId: string;
  prisma: PrismaClient;
  character: {
    level: number;
    currentStreak: number;
    intellect: number;
    strength: number;
    discipline: number;
    creativity: number;
    social: number;
    recovery: number;
    createdAt: Date;
  };
  completionTime?: Date; // timestamp of this completion
}

type TraitConditionFn = (ctx: TraitContext) => Promise<boolean>;

export const TRAIT_CONDITION_MAP: Record<string, TraitConditionFn> = {
  // DEEP WORKER: 10+ INTELLECT quest completions in the last 7 days
  [TRAIT_CONDITIONS.DEEP_WORKER]: async ({ userId, prisma }) => {
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    const count = await prisma.questCompletion.count({
      where: {
        userId,
        quest: { attribute: 'INTELLECT' },
        completedAt: { gte: sevenDaysAgo },
      },
    });
    return count >= 10;
  },

  // RELENTLESS: 30-day streak
  [TRAIT_CONDITIONS.RELENTLESS]: async ({ character }) => {
    return character.currentStreak >= 30;
  },

  // ATHLETE: 20+ STRENGTH quest completions total
  [TRAIT_CONDITIONS.ATHLETE]: async ({ userId, prisma }) => {
    const count = await prisma.questCompletion.count({
      where: { userId, quest: { attribute: 'STRENGTH' } },
    });
    return count >= 20;
  },

  // CREATOR: 15+ CREATIVITY quest completions total
  [TRAIT_CONDITIONS.CREATOR]: async ({ userId, prisma }) => {
    const count = await prisma.questCompletion.count({
      where: { userId, quest: { attribute: 'CREATIVITY' } },
    });
    return count >= 15;
  },

  // GENERALIST: All 6 attributes ≥ 30
  [TRAIT_CONDITIONS.GENERALIST]: async ({ character }) => {
    return (
      character.intellect >= 30 &&
      character.strength >= 30 &&
      character.discipline >= 30 &&
      character.creativity >= 30 &&
      character.social >= 30 &&
      character.recovery >= 30
    );
  },

  // FAST LEARNER: Level 10 within 30 days of account creation
  [TRAIT_CONDITIONS.FAST_LEARNER]: async ({ character }) => {
    const daysSinceCreation = Math.floor(
      (Date.now() - character.createdAt.getTime()) / (1000 * 60 * 60 * 24)
    );
    return character.level >= 10 && daysSinceCreation <= 30;
  },

  // BALANCED: No single attribute > 2x any other
  [TRAIT_CONDITIONS.BALANCED]: async ({ character }) => {
    const attrs = [
      character.intellect,
      character.strength,
      character.discipline,
      character.creativity,
      character.social,
      character.recovery,
    ];
    const max = Math.max(...attrs);
    const min = Math.min(...attrs);
    return min > 0 && max / min <= 2.0;
  },

  // BUILDER: 10+ quests linked to a campaign completed
  [TRAIT_CONDITIONS.BUILDER]: async ({ userId, prisma }) => {
    const count = await prisma.questCompletion.count({
      where: {
        userId,
        quest: { campaignId: { not: null } },
      },
    });
    return count >= 10;
  },

  // NIGHT OWL: 10+ completions after 10 PM
  [TRAIT_CONDITIONS.NIGHT_OWL]: async ({ userId, prisma }) => {
    const allCompletions = await prisma.questCompletion.findMany({
      where: { userId },
      select: { completedAt: true },
    });
    const nightCount = allCompletions.filter((c) => {
      const hour = c.completedAt.getHours();
      return hour >= 22 || hour < 3;
    }).length;
    return nightCount >= 10;
  },

  // EARLY RISER: 10+ completions before 7 AM
  [TRAIT_CONDITIONS.EARLY_RISER]: async ({ userId, prisma }) => {
    const allCompletions = await prisma.questCompletion.findMany({
      where: { userId },
      select: { completedAt: true },
    });
    const earlyCount = allCompletions.filter((c) => {
      const hour = c.completedAt.getHours();
      return hour >= 4 && hour < 7;
    }).length;
    return earlyCount >= 10;
  },

  // SOCIAL BUTTERFLY: 15+ SOCIAL quest completions total
  [TRAIT_CONDITIONS.SOCIAL_BUTTERFLY]: async ({ userId, prisma }) => {
    const count = await prisma.questCompletion.count({
      where: { userId, quest: { attribute: 'SOCIAL' } },
    });
    return count >= 15;
  },
};

// ─── Main Evaluation ──────────────────────────────────────────────────────────

export async function evaluateTraits(
  ctx: TraitContext
): Promise<string[]> {
  const { userId, prisma } = ctx;

  // Get all traits
  const allTraits = await prisma.trait.findMany();

  // Get already-unlocked traits
  const existingTraits = await prisma.userTrait.findMany({
    where: { userId },
    select: { traitId: true },
  });
  const unlockedSet = new Set(existingTraits.map((t) => t.traitId));

  const newlyUnlocked: string[] = [];

  for (const trait of allTraits) {
    // Skip already unlocked
    if (unlockedSet.has(trait.id)) continue;

    const conditionFn = TRAIT_CONDITION_MAP[trait.conditionKey];
    if (!conditionFn) continue;

    try {
      const met = await conditionFn(ctx);
      if (met) {
        newlyUnlocked.push(trait.id);
      }
    } catch {
      // Trait evaluation errors are non-fatal
    }
  }

  return newlyUnlocked;
}
