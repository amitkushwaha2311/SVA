// LIFE//OS — Weekly Report API

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const userId = session.user.id;
  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

  // Get week's completions
  const completions = await prisma.questCompletion.findMany({
    where: { userId, completedAt: { gte: oneWeekAgo } },
    include: { quest: { select: { attribute: true, title: true, difficulty: true } } },
  });

  const character = await prisma.character.findUnique({ where: { userId } });
  if (!character) {
    return NextResponse.json({ error: 'Character not found.' }, { status: 404 });
  }

  // Calculate stats
  const totalXP = completions.reduce((sum, c) => sum + c.xpEarned, 0);
  const totalGold = completions.reduce((sum, c) => sum + c.goldEarned, 0);
  const questsCompleted = completions.length;

  // Attribute breakdown
  const attrCounts: Record<string, number> = {
    INTELLECT: 0, STRENGTH: 0, DISCIPLINE: 0, CREATIVITY: 0, SOCIAL: 0, RECOVERY: 0,
  };
  for (const c of completions) {
    attrCounts[c.quest.attribute] = (attrCounts[c.quest.attribute] ?? 0) + 1;
  }

  const sortedAttrs = Object.entries(attrCounts).sort((a, b) => b[1] - a[1]);
  const bestAttr = sortedAttrs[0]?.[0] ?? null;
  const weakestAttr = sortedAttrs[sortedAttrs.length - 1]?.[0] ?? null;

  // Best day by XP
  const dayXP: Record<string, number> = {};
  for (const c of completions) {
    const day = c.completedAt.toISOString().split('T')[0];
    dayXP[day] = (dayXP[day] ?? 0) + c.xpEarned;
  }
  const bestDay = Object.entries(dayXP).sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;

  // New traits this week
  const newTraits = await prisma.userTrait.findMany({
    where: { userId, unlockedAt: { gte: oneWeekAgo } },
    include: { trait: true },
  });

  // Recommendation
  const recommendations: Record<string, { title: string; attribute: string; xp: number }> = {
    INTELLECT: { title: 'Read for 20 minutes', attribute: 'INTELLECT', xp: 30 },
    STRENGTH: { title: 'Complete a full workout', attribute: 'STRENGTH', xp: 60 },
    DISCIPLINE: { title: 'Wake up before 7 AM 3 days', attribute: 'DISCIPLINE', xp: 60 },
    CREATIVITY: { title: 'Create something — draw, write, or build', attribute: 'CREATIVITY', xp: 60 },
    SOCIAL: { title: 'Have a meaningful conversation', attribute: 'SOCIAL', xp: 30 },
    RECOVERY: { title: 'Sleep before midnight × 3 days', attribute: 'RECOVERY', xp: 60 },
  };
  const recommendation = weakestAttr ? recommendations[weakestAttr] : null;

  return NextResponse.json({
    weekNumber: Math.ceil((new Date().getTime() - new Date(new Date().getFullYear(), 0, 1).getTime()) / (7 * 24 * 60 * 60 * 1000)),
    totalXP,
    totalGold,
    questsCompleted,
    bestAttr,
    weakestAttr,
    bestDay,
    currentStreak: character.currentStreak,
    longestStreak: character.longestStreak,
    newTraits: newTraits.map((t) => t.trait),
    attrBreakdown: attrCounts,
    recommendation,
    dayXP,
  });
}
