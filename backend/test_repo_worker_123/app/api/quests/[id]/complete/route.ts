// LIFE//OS — Quest Complete API
// Server-authoritative progression calculation

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import {
  processQuestCompletion,
  getTodayString,
} from '@/lib/game-engine';
import { evaluateTraits } from '@/lib/trait-engine';
import { calculateBossDamage, applyBossDamage } from '@/lib/boss-engine';
import { requiredXPForLevel } from '@/lib/constants';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: questId } = await params;
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const userId = session.user.id;

  try {
    // ── 1. Load quest with ownership check ─────────────────────────────────
    const quest = await prisma.quest.findFirst({
      where: { id: questId, userId },
    });

    if (!quest) {
      return NextResponse.json({ error: 'Quest not found.' }, { status: 404 });
    }

    // ── 2. Verify quest state & protection against same-day duplicate completion ──
    if (quest.status === 'CANCELLED') {
      return NextResponse.json(
        { error: 'This quest has been cancelled.' },
        { status: 409 }
      );
    }

    const today = getTodayString();
    const startOfDay = new Date(`${today}T00:00:00.000Z`);
    const endOfDay = new Date(`${today}T23:59:59.999Z`);

    const existingCompletionToday = await prisma.questCompletion.findFirst({
      where: {
        questId,
        userId,
        completedAt: {
          gte: startOfDay,
          lte: endOfDay,
        },
      },
    });

    if (existingCompletionToday) {
      return NextResponse.json(
        { error: 'You have already completed this quest today.' },
        { status: 409 }
      );
    }

    // ── 3. Load character ───────────────────────────────────────────────────
    const character = await prisma.character.findUnique({
      where: { userId },
      include: { user: { select: { createdAt: true } } },
    });

    if (!character) {
      return NextResponse.json({ error: 'Character not found.' }, { status: 404 });
    }

    // ── 4. Calculate progression (server-authoritative) ────────────────────
    const progression = processQuestCompletion(
      {
        level: character.level,
        xp: character.xp,
        xpToNextLevel: character.xpToNextLevel,
        gold: character.gold,
        intellect: character.intellect,
        strength: character.strength,
        discipline: character.discipline,
        creativity: character.creativity,
        social: character.social,
        recovery: character.recovery,
        currentStreak: character.currentStreak,
        longestStreak: character.longestStreak,
        lastActiveDate: character.lastActiveDate,
        comboMultiplier: character.comboMultiplier,
      },
      quest.difficulty,
      quest.attribute,
      today
    );

    const { rewards, streakResult, levelUpResult, newCharacter } = progression;

    // ── 5. Load active bosses & calculate damage ────────────────────────────
    const activeBosses = await prisma.boss.findMany({
      where: { userId, status: 'ACTIVE' },
    });

    const bossDamageResults: Array<{
      bossId: string;
      damage: number;
      newHP: number;
      defeated: boolean;
      name: string;
      rewardXP: number;
      rewardGold: number;
    }> = [];

    for (const boss of activeBosses) {
      const damage = calculateBossDamage(quest.attribute, quest.difficulty);
      const { newHP, defeated } = applyBossDamage(boss.currentHP, boss.maxHP, damage);
      bossDamageResults.push({
        bossId: boss.id,
        damage,
        newHP,
        defeated,
        name: boss.name,
        rewardXP: defeated ? boss.rewardXP : 0,
        rewardGold: defeated ? boss.rewardGold : 0,
      });
    }

    // ── 6. Evaluate trait conditions ────────────────────────────────────────
    const newTraitIds = await evaluateTraits({
      userId,
      prisma,
      character: {
        level: newCharacter.level,
        currentStreak: newCharacter.currentStreak,
        intellect: newCharacter.intellect,
        strength: newCharacter.strength,
        discipline: newCharacter.discipline,
        creativity: newCharacter.creativity,
        social: newCharacter.social,
        recovery: newCharacter.recovery,
        createdAt: (character as unknown as { user: { createdAt: Date } }).user.createdAt,
      },
      completionTime: new Date(),
    });

    // Load new trait details
    const newTraits = newTraitIds.length > 0
      ? await prisma.trait.findMany({ where: { id: { in: newTraitIds } } })
      : [];

    // ── 7. Check ability unlocks ────────────────────────────────────────────
    let newAbilities: Array<{ id: string; name: string; description: string; icon: string }> = [];
    if (levelUpResult.levelsGained > 0) {
      const allAbilities = await prisma.ability.findMany({
        where: {
          requiredLevel: {
            gt: character.level,
            lte: newCharacter.level,
          },
        },
      });
      const existingAbilities = await prisma.userAbility.findMany({
        where: { userId },
        select: { abilityId: true },
      });
      const existingSet = new Set(existingAbilities.map((a) => a.abilityId));
      newAbilities = allAbilities.filter((a) => !existingSet.has(a.id));
    }

    // ── 8. Calculate boss defeat rewards ────────────────────────────────────
    const defeatedBosses = bossDamageResults.filter((b) => b.defeated);
    const bossXPBonus = defeatedBosses.reduce((sum, b) => sum + b.rewardXP, 0);
    const bossGoldBonus = defeatedBosses.reduce((sum, b) => sum + b.rewardGold, 0);

    // Apply boss rewards to character
    let finalGold = newCharacter.gold + bossGoldBonus;
    let finalXP = newCharacter.xp;
    let finalLevel = newCharacter.level;
    let finalXPToNext = newCharacter.xpToNextLevel;

    if (bossXPBonus > 0) {
      let xp = newCharacter.xp + bossXPBonus;
      let level = newCharacter.level;
      while (xp >= requiredXPForLevel(level)) {
        xp -= requiredXPForLevel(level);
        level++;
        finalGold += 100;
      }
      finalXP = xp;
      finalLevel = level;
      finalXPToNext = requiredXPForLevel(level);
    }

    // ── 9. Atomic database write ────────────────────────────────────────────
    await prisma.$transaction(async (tx) => {
      // Mark quest completed
      await tx.quest.update({
        where: { id: questId },
        data: { status: 'COMPLETED' },
      });

      // Create completion record
      await tx.questCompletion.create({
        data: {
          questId,
          userId,
          xpEarned: rewards.xpFinal,
          goldEarned: rewards.goldFinal,
          comboApplied: rewards.comboUsed,
        },
      });

      // Update character
      await tx.character.update({
        where: { userId },
        data: {
          level: finalLevel,
          xp: finalXP,
          xpToNextLevel: finalXPToNext,
          gold: finalGold,
          intellect: newCharacter.intellect,
          strength: newCharacter.strength,
          discipline: newCharacter.discipline,
          creativity: newCharacter.creativity,
          social: newCharacter.social,
          recovery: newCharacter.recovery,
          currentStreak: newCharacter.currentStreak,
          longestStreak: newCharacter.longestStreak,
          lastActiveDate: today,
          comboMultiplier: newCharacter.comboMultiplier,
        },
      });

      // Update bosses
      for (const bdr of bossDamageResults) {
        await tx.boss.update({
          where: { id: bdr.bossId },
          data: {
            currentHP: bdr.newHP,
            status: bdr.defeated ? 'DEFEATED' : 'ACTIVE',
          },
        });

        await tx.bossDamageEvent.create({
          data: {
            bossId: bdr.bossId,
            userId,
            questId,
            damage: bdr.damage,
          },
        });
      }

      // Unlock new traits
      for (const traitId of newTraitIds) {
        await tx.userTrait.create({
          data: { userId, traitId },
        });
      }

      // Unlock new abilities
      for (const ability of newAbilities) {
        await tx.userAbility.create({
          data: { userId, abilityId: ability.id },
        });
      }

      // Activity events
      await tx.activityEvent.create({
        data: {
          userId,
          type: 'QUEST_COMPLETED',
          metadata: JSON.stringify({
            questId,
            questTitle: quest.title,
            attribute: quest.attribute,
            difficulty: quest.difficulty,
            xpEarned: rewards.xpFinal,
            goldEarned: rewards.goldFinal,
            combo: rewards.comboUsed,
          }),
        },
      });

      if (rewards.xpFinal > 0) {
        await tx.activityEvent.create({
          data: {
            userId,
            type: 'XP_GAINED',
            metadata: JSON.stringify({ amount: rewards.xpFinal, total: finalXP }),
          },
        });
      }

      if (levelUpResult.levelsGained > 0) {
        await tx.activityEvent.create({
          data: {
            userId,
            type: 'LEVEL_UP',
            metadata: JSON.stringify({
              fromLevel: character.level,
              toLevel: newCharacter.level,
              goldBonus: levelUpResult.goldBonus,
            }),
          },
        });
      }

      if (rewards.attributeGain > 0) {
        await tx.activityEvent.create({
          data: {
            userId,
            type: 'ATTRIBUTE_INCREASED',
            metadata: JSON.stringify({
              attribute: quest.attribute,
              gain: rewards.attributeGain,
            }),
          },
        });
      }

      for (const trait of newTraits) {
        await tx.activityEvent.create({
          data: {
            userId,
            type: 'TRAIT_UNLOCKED',
            metadata: JSON.stringify({ traitId: trait.id, traitName: trait.name, traitIcon: trait.icon }),
          },
        });
      }

      for (const bdr of defeatedBosses) {
        await tx.activityEvent.create({
          data: {
            userId,
            type: 'BOSS_DEFEATED',
            metadata: JSON.stringify({ bossId: bdr.bossId, bossName: bdr.name, rewardXP: bdr.rewardXP, rewardGold: bdr.rewardGold }),
          },
        });
      }

      if (streakResult.milestoneReached) {
        await tx.activityEvent.create({
          data: {
            userId,
            type: 'STREAK_MILESTONE',
            metadata: JSON.stringify({ streak: streakResult.milestoneReached }),
          },
        });
      }
    });

    // ── 10. Return result ───────────────────────────────────────────────────
    return NextResponse.json({
      success: true,
      rewards: {
        xpEarned: rewards.xpFinal,
        goldEarned: rewards.goldFinal + bossGoldBonus,
        combo: rewards.comboUsed,
        attributeGain: rewards.attributeGain,
        attribute: quest.attribute,
      },
      character: {
        level: finalLevel,
        xp: finalXP,
        xpToNextLevel: finalXPToNext,
        gold: finalGold,
        currentStreak: newCharacter.currentStreak,
        longestStreak: newCharacter.longestStreak,
        comboMultiplier: newCharacter.comboMultiplier,
        intellect: newCharacter.intellect,
        strength: newCharacter.strength,
        discipline: newCharacter.discipline,
        creativity: newCharacter.creativity,
        social: newCharacter.social,
        recovery: newCharacter.recovery,
      },
      levelUp: levelUpResult.levelsGained > 0 ? {
        levelsGained: levelUpResult.levelsGained,
        fromLevel: character.level,
        toLevel: finalLevel,
        goldBonus: levelUpResult.goldBonus,
        newAbilities,
      } : null,
      newTraits,
      bossDamage: bossDamageResults,
      defeatedBosses,
      streakMilestone: streakResult.milestoneReached,
    });
  } catch (error) {
    console.error('[QUEST COMPLETE ERROR]', error);
    return NextResponse.json(
      { error: 'Failed to complete quest. Your progress is safe.' },
      { status: 500 }
    );
  }
}
