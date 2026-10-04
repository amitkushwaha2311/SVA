// LIFE//OS — Habit Complete API
// Server-authoritative habit progression calculation with duplicate protection

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { getTodayString, processLevelUps } from '@/lib/game-engine';
import { getComboMultiplier } from '@/lib/constants';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: habitId } = await params;
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const userId = session.user.id;
  const today = getTodayString();
  const startOfDay = new Date(`${today}T00:00:00.000Z`);
  const endOfDay = new Date(`${today}T23:59:59.999Z`);

  try {
    // ── 1. Load habit with ownership check ─────────────────────────────────
    const habit = await prisma.habit.findFirst({
      where: { id: habitId, userId },
    });

    if (!habit) {
      return NextResponse.json({ error: 'Habit not found.' }, { status: 404 });
    }

    // ── 2. Duplicate completion check for today ────────────────────────────
    const existingCompletionToday = await prisma.habitCompletion.findFirst({
      where: {
        habitId,
        userId,
        completedAt: {
          gte: startOfDay,
          lte: endOfDay,
        },
      },
    });

    if (existingCompletionToday) {
      return NextResponse.json(
        { error: 'You have already completed this habit today.' },
        { status: 409 }
      );
    }

    // ── 3. Load character ───────────────────────────────────────────────────
    const character = await prisma.character.findUnique({
      where: { userId },
    });

    if (!character) {
      return NextResponse.json({ error: 'Character not found.' }, { status: 404 });
    }

    // ── 4. Calculate habit streak & rewards (server-side) ───────────────────
    let newHabitStreak = habit.currentStreak + 1;
    let habitStreakBroken = false;

    if (habit.lastCompletedAt) {
      const lastCompletedDate = habit.lastCompletedAt.toISOString().split('T')[0];
      const last = new Date(lastCompletedDate);
      const todayDate = new Date(today);
      const diffMs = todayDate.getTime() - last.getTime();
      const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays > (habit.frequency === 'WEEKLY' ? 7 : 1)) {
        newHabitStreak = 1;
        habitStreakBroken = true;
      }
    }

    const newLongestHabitStreak = Math.max(habit.longestStreak, newHabitStreak);
    const combo = getComboMultiplier(newHabitStreak);

    const xpEarned = Math.floor(habit.xpReward * combo);
    const goldEarned = Math.floor(habit.goldReward * combo);
    const attributeGain = habit.difficulty === 'EPIC' ? 3 : habit.difficulty === 'HARD' ? 2 : 1;

    // Process character level up
    const levelResult = processLevelUps(character.level, character.xp, xpEarned);

    // Apply attribute boost
    const attrKey = habit.attribute.toLowerCase() as 'intellect' | 'strength' | 'discipline' | 'creativity' | 'social' | 'recovery';
    const currentAttrVal = character[attrKey] ?? 10;
    const updatedAttrVal = currentAttrVal + attributeGain;

    const finalGold = character.gold + goldEarned + levelResult.goldBonus;

    // ── 5. Atomic database transaction ─────────────────────────────────────
    await prisma.$transaction(async (tx) => {
      // Record habit completion
      await tx.habitCompletion.create({
        data: {
          habitId,
          userId,
          xpEarned,
          goldEarned,
        },
      });

      // Update habit streaks
      await tx.habit.update({
        where: { id: habitId },
        data: {
          currentStreak: newHabitStreak,
          longestStreak: newLongestHabitStreak,
          lastCompletedAt: new Date(),
        },
      });

      // Update character state
      await tx.character.update({
        where: { userId },
        data: {
          level: levelResult.newLevel,
          xp: levelResult.newXP,
          xpToNextLevel: levelResult.xpToNextLevel,
          gold: finalGold,
          [attrKey]: updatedAttrVal,
          lastActiveDate: today,
        },
      });

      // Log activity events
      await tx.activityEvent.create({
        data: {
          userId,
          type: 'HABIT_COMPLETED',
          metadata: JSON.stringify({
            habitId,
            title: habit.title,
            attribute: habit.attribute,
            xpEarned,
            goldEarned,
            streak: newHabitStreak,
          }),
        },
      });

      if (levelResult.levelsGained > 0) {
        await tx.activityEvent.create({
          data: {
            userId,
            type: 'LEVEL_UP',
            metadata: JSON.stringify({
              fromLevel: character.level,
              toLevel: levelResult.newLevel,
              goldBonus: levelResult.goldBonus,
            }),
          },
        });
      }
    });

    return NextResponse.json({
      success: true,
      rewards: {
        xpEarned,
        goldEarned,
        attribute: habit.attribute,
        attributeGain,
      },
      habit: {
        id: habitId,
        currentStreak: newHabitStreak,
        longestStreak: newLongestHabitStreak,
        lastCompletedAt: new Date().toISOString(),
      },
      character: {
        level: levelResult.newLevel,
        xp: levelResult.newXP,
        xpToNextLevel: levelResult.xpToNextLevel,
        gold: finalGold,
        [attrKey]: updatedAttrVal,
      },
      levelUp: levelResult.levelsGained > 0 ? {
        levelsGained: levelResult.levelsGained,
        newLevel: levelResult.newLevel,
        goldBonus: levelResult.goldBonus,
      } : null,
    });
  } catch (error) {
    console.error('[HABIT COMPLETE ERROR]', error);
    return NextResponse.json(
      { error: 'Failed to complete habit. Progress safe.' },
      { status: 500 }
    );
  }
}
