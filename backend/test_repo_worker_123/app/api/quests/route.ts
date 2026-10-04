// LIFE//OS — Quests API (GET list + POST create)

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';
import { DIFFICULTY_XP, DIFFICULTY_GOLD } from '@/lib/constants';

const createQuestSchema = z.object({
  title: z.string().min(1, 'Every quest needs a name.').max(200),
  description: z.string().max(1000).optional(),
  attribute: z.enum(['INTELLECT', 'STRENGTH', 'DISCIPLINE', 'CREATIVITY', 'SOCIAL', 'RECOVERY']),
  difficulty: z.enum(['EASY', 'MEDIUM', 'HARD', 'EPIC']),
  dueDate: z.string().datetime().optional().nullable(),
  campaignId: z.string().optional().nullable(),
});

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const status = searchParams.get('status') ?? 'ACTIVE';
  const campaignId = searchParams.get('campaignId');

  const quests = await prisma.quest.findMany({
    where: {
      userId: session.user.id,
      status,
      ...(campaignId ? { campaignId } : {}),
    },
    include: {
      completions: {
        select: { completedAt: true, xpEarned: true, goldEarned: true },
        take: 1,
      },
    },
    orderBy: [
      { dueDate: 'asc' },
      { createdAt: 'desc' },
    ],
  });

  return NextResponse.json({ quests });
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const parsed = createQuestSchema.safeParse(body);

    if (!parsed.success) {
      const firstError = Object.values(parsed.error.flatten().fieldErrors)[0]?.[0];
      return NextResponse.json(
        { error: firstError ?? 'Invalid quest data.' },
        { status: 400 }
      );
    }

    const { title, description, attribute, difficulty, dueDate, campaignId } = parsed.data;

    // If campaignId is provided, verify ownership
    if (campaignId) {
      const campaign = await prisma.campaign.findFirst({
        where: { id: campaignId, userId: session.user.id },
      });
      if (!campaign) {
        return NextResponse.json({ error: 'Campaign not found.' }, { status: 404 });
      }
    }

    const quest = await prisma.quest.create({
      data: {
        userId: session.user.id,
        title,
        description,
        attribute,
        difficulty,
        xpReward: DIFFICULTY_XP[difficulty],
        goldReward: DIFFICULTY_GOLD[difficulty],
        dueDate: dueDate ? new Date(dueDate) : null,
        campaignId: campaignId ?? null,
      },
    });

    return NextResponse.json({ quest }, { status: 201 });
  } catch (error) {
    console.error('[QUEST CREATE ERROR]', error);
    return NextResponse.json(
      { error: 'Failed to create quest.' },
      { status: 500 }
    );
  }
}
