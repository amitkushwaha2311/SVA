// LIFE//OS — Bosses API

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

const createBossSchema = z.object({
  name: z.string().min(1, 'Every boss needs a name.').max(100),
  description: z.string().max(500).optional(),
  maxHP: z.number().int().min(100).max(10000).default(1000),
  rewardXP: z.number().int().min(0).default(500),
  rewardGold: z.number().int().min(0).default(200),
});

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const bosses = await prisma.boss.findMany({
    where: { userId: session.user.id },
    include: {
      damageEvents: {
        orderBy: { createdAt: 'desc' },
        take: 10,
        include: { quest: { select: { title: true, attribute: true } } },
      },
    },
    orderBy: { createdAt: 'desc' },
  });

  return NextResponse.json({ bosses });
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const parsed = createBossSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid boss data.' }, { status: 400 });
    }

    const { name, description, maxHP, rewardXP, rewardGold } = parsed.data;

    const boss = await prisma.boss.create({
      data: {
        userId: session.user.id,
        name,
        description,
        maxHP,
        currentHP: maxHP,
        rewardXP,
        rewardGold,
      },
    });

    return NextResponse.json({ boss }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to create boss.' }, { status: 500 });
  }
}
