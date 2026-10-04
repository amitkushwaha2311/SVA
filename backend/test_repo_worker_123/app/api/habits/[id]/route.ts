// LIFE//OS — Habit [id] API (GET, PATCH, DELETE)

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

const updateHabitSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  description: z.string().max(1000).optional(),
  attribute: z.enum(['INTELLECT', 'STRENGTH', 'DISCIPLINE', 'CREATIVITY', 'SOCIAL', 'RECOVERY']).optional(),
  difficulty: z.enum(['EASY', 'MEDIUM', 'HARD', 'EPIC']).optional(),
  frequency: z.enum(['DAILY', 'WEEKLY']).optional(),
});

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const habit = await prisma.habit.findFirst({
    where: { id, userId: session.user.id },
    include: {
      completions: { orderBy: { completedAt: 'desc' } },
    },
  });

  if (!habit) {
    return NextResponse.json({ error: 'Habit not found.' }, { status: 404 });
  }

  return NextResponse.json({ habit });
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const habit = await prisma.habit.findFirst({
    where: { id, userId: session.user.id },
  });

  if (!habit) {
    return NextResponse.json({ error: 'Habit not found.' }, { status: 404 });
  }

  try {
    const body = await req.json();
    const parsed = updateHabitSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid habit data.' }, { status: 400 });
    }

    const updated = await prisma.habit.update({
      where: { id },
      data: parsed.data,
    });

    return NextResponse.json({ habit: updated });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to update habit.' }, { status: 500 });
  }
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const habit = await prisma.habit.findFirst({
    where: { id, userId: session.user.id },
  });

  if (!habit) {
    return NextResponse.json({ error: 'Habit not found.' }, { status: 404 });
  }

  await prisma.habit.delete({ where: { id } });

  return NextResponse.json({ message: 'Habit deleted.' });
}
