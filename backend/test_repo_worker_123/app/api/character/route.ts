// LIFE//OS — Character API

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const character = await prisma.character.findUnique({
    where: { userId: session.user.id },
  });

  if (!character) {
    return NextResponse.json({ error: 'Character not found.' }, { status: 404 });
  }

  const traits = await prisma.userTrait.findMany({
    where: { userId: session.user.id },
    include: { trait: true },
    orderBy: { unlockedAt: 'desc' },
  });

  const abilities = await prisma.userAbility.findMany({
    where: { userId: session.user.id },
    include: { ability: true },
    orderBy: { unlockedAt: 'desc' },
  });

  const questStats = await prisma.questCompletion.count({
    where: { userId: session.user.id },
  });

  return NextResponse.json({
    character,
    traits: traits.map((t) => t.trait),
    abilities: abilities.map((a) => a.ability),
    questsCompleted: questStats,
  });
}

export async function PATCH(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const { archetype } = body;

    if (!archetype) {
      return NextResponse.json({ error: 'Invalid data.' }, { status: 400 });
    }

    const updated = await prisma.character.update({
      where: { userId: session.user.id },
      data: { archetype },
    });

    return NextResponse.json({ character: updated });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to update character.' }, { status: 500 });
  }
}
