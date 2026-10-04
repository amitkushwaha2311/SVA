// LIFE//OS — Quest [id] API (GET, PATCH, DELETE)

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

const updateQuestSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  description: z.string().max(1000).optional(),
  attribute: z.enum(['INTELLECT', 'STRENGTH', 'DISCIPLINE', 'CREATIVITY', 'SOCIAL', 'RECOVERY']).optional(),
  difficulty: z.enum(['EASY', 'MEDIUM', 'HARD', 'EPIC']).optional(),
  dueDate: z.string().datetime().optional().nullable(),
  status: z.enum(['ACTIVE', 'CANCELLED']).optional(),
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

  const quest = await prisma.quest.findFirst({
    where: { id, userId: session.user.id },
    include: {
      completions: true,
      campaign: { select: { id: true, name: true } },
    },
  });

  if (!quest) {
    return NextResponse.json({ error: 'Quest not found.' }, { status: 404 });
  }

  return NextResponse.json({ quest });
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

  const quest = await prisma.quest.findFirst({
    where: { id, userId: session.user.id },
  });

  if (!quest) {
    return NextResponse.json({ error: 'Quest not found.' }, { status: 404 });
  }

  if (quest.status === 'COMPLETED') {
    return NextResponse.json({ error: 'Cannot edit a completed quest.' }, { status: 409 });
  }

  try {
    const body = await req.json();
    const parsed = updateQuestSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid data.' }, { status: 400 });
    }

    const updated = await prisma.quest.update({
      where: { id },
      data: {
        ...parsed.data,
        dueDate: parsed.data.dueDate ? new Date(parsed.data.dueDate) : undefined,
      },
    });

    return NextResponse.json({ quest: updated });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to update quest.' }, { status: 500 });
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

  const quest = await prisma.quest.findFirst({
    where: { id, userId: session.user.id },
  });

  if (!quest) {
    return NextResponse.json({ error: 'Quest not found.' }, { status: 404 });
  }

  await prisma.quest.delete({ where: { id } });

  return NextResponse.json({ message: 'Quest deleted.' });
}
