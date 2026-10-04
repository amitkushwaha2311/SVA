// LIFE//OS — Habits API (GET, POST)

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

const createHabitSchema = z.object({
  title: z.string().min(1, 'Title is required.').max(200),
  description: z.string().max(1000).optional(),
  attribute: z.enum(['INTELLECT', 'STRENGTH', 'DISCIPLINE', 'CREATIVITY', 'SOCIAL', 'RECOVERY']),
  difficulty: z.enum(['EASY', 'MEDIUM', 'HARD', 'EPIC']).default('MEDIUM'),
  frequency: z.enum(['DAILY', 'WEEKLY']).default('DAILY'),
});

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const habits = await prisma.habit.findMany({
    where: { userId: session.user.id },
    include: {
      completions: {
        orderBy: { completedAt: 'desc' },
        take: 10,
      },
    },
    orderBy: { createdAt: 'desc' },
  });

  return NextResponse.json({ habits });
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const parsed = createHabitSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Invalid habit data', details: parsed.error.flatten() },
        { status: 400 }
      );
    }

    const { title, description, attribute, difficulty, frequency } = parsed.data;

    // Difficulty reward mapping
    const xpRewards: Record<string, number> = { EASY: 25, MEDIUM: 45, HARD: 80, EPIC: 150 };
    const goldRewards: Record<string, number> = { EASY: 10, MEDIUM: 20, HARD: 40, EPIC: 80 };

    const habit = await prisma.habit.create({
      data: {
        userId: session.user.id,
        title,
        description,
        attribute,
        difficulty,
        frequency,
        xpReward: xpRewards[difficulty] ?? 45,
        goldReward: goldRewards[difficulty] ?? 20,
      },
    });

    return NextResponse.json({ habit }, { status: 201 });
  } catch (error) {
    console.error('[HABIT CREATE ERROR]', error);
    return NextResponse.json(
      { error: 'Failed to create habit.' },
      { status: 500 }
    );
  }
}
