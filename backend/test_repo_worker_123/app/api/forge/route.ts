// LIFE//OS — Quest Forge API

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { forgeFromGoal } from '@/lib/forge';
import { z } from 'zod';

const forgeSchema = z.object({
  goal: z.string().min(3, 'Please describe your goal.').max(500),
  createCampaign: z.boolean().default(true),
});

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const parsed = forgeSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: 'Please describe your goal.' }, { status: 400 });
    }

    const userId = session.user.id;
    const { goal, createCampaign } = parsed.data;
    const forged = forgeFromGoal({ goal, userId });

    if (!createCampaign) {
      // Just return the suggestion
      return NextResponse.json({ suggestion: forged });
    }

    // Actually create the campaign + quests in the database
    const campaign = await prisma.$transaction(async (tx) => {
      const newCampaign = await tx.campaign.create({
        data: {
          userId,
          name: forged.name,
          description: forged.description,
        },
      });

      // Create stages
      await tx.campaignStage.createMany({
        data: forged.stages.map((s, i) => ({
          campaignId: newCampaign.id,
          name: s.name,
          description: s.description,
          order: s.order,
          status: i === 0 ? 'ACTIVE' : 'LOCKED',
        })),
      });

      // Create quests linked to campaign
      await tx.quest.createMany({
        data: forged.quests.map((q) => ({
          userId,
          campaignId: newCampaign.id,
          title: q.title,
          description: q.description,
          attribute: q.attribute,
          difficulty: q.difficulty,
          xpReward: q.xpReward,
          goldReward: q.goldReward,
        })),
      });

      return tx.campaign.findUnique({
        where: { id: newCampaign.id },
        include: {
          stages: { orderBy: { order: 'asc' } },
          quests: true,
        },
      });
    });

    return NextResponse.json({ campaign, forged }, { status: 201 });
  } catch (error) {
    console.error('[FORGE ERROR]', error);
    return NextResponse.json({ error: 'Quest Forge failed. Please try again.' }, { status: 500 });
  }
}
