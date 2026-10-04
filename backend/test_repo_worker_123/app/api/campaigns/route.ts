// LIFE//OS — Campaigns API

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

const createCampaignSchema = z.object({
  name: z.string().min(1, 'Campaign needs a name.').max(200),
  description: z.string().max(1000).optional(),
  stages: z.array(z.object({
    name: z.string().min(1),
    description: z.string().optional(),
    order: z.number().int().positive(),
  })).optional(),
});

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const campaigns = await prisma.campaign.findMany({
    where: { userId: session.user.id },
    include: {
      stages: { orderBy: { order: 'asc' } },
      quests: {
        where: { status: 'COMPLETED' },
        select: { id: true },
      },
      _count: { select: { quests: true } },
    },
    orderBy: { createdAt: 'desc' },
  });

  // Calculate real progress
  const campaignsWithProgress = campaigns.map((c) => {
    const totalStages = c.stages.length;
    const completedStages = c.stages.filter((s) => s.status === 'COMPLETED').length;
    const progress = totalStages > 0 ? Math.round((completedStages / totalStages) * 100) : 0;
    return { ...c, progress };
  });

  return NextResponse.json({ campaigns: campaignsWithProgress });
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const parsed = createCampaignSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid campaign data.' }, { status: 400 });
    }

    const userId = session.user.id;
    const { name, description, stages = [] } = parsed.data;

    const campaign = await prisma.$transaction(async (tx) => {
      const newCampaign = await tx.campaign.create({
        data: {
          userId,
          name,
          description,
        },
      });

      if (stages.length > 0) {
        await tx.campaignStage.createMany({
          data: stages.map((s, i) => ({
            campaignId: newCampaign.id,
            name: s.name,
            description: s.description,
            order: s.order ?? i + 1,
            status: i === 0 ? 'ACTIVE' : 'LOCKED',
          })),
        });
      }

      return tx.campaign.findUnique({
        where: { id: newCampaign.id },
        include: { stages: { orderBy: { order: 'asc' } } },
      });
    });

    return NextResponse.json({ campaign }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to create campaign.' }, { status: 500 });
  }
}
