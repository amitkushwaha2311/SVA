// LIFE//OS — History/Timeline API

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const limit = Math.min(parseInt(searchParams.get('limit') ?? '50'), 100);
  const cursor = searchParams.get('cursor');

  const events = await prisma.activityEvent.findMany({
    where: { userId: session.user.id },
    orderBy: { createdAt: 'desc' },
    take: limit,
    ...(cursor ? { skip: 1, cursor: { id: cursor } } : {}),
  });

  return NextResponse.json({
    events: events.map((e) => ({
      ...e,
      metadata: JSON.parse(e.metadata),
    })),
    nextCursor: events.length === limit ? events[events.length - 1].id : null,
  });
}
