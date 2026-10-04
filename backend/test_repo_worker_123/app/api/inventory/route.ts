// LIFE//OS — Inventory API (GET + equip/unequip)

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const inventory = await prisma.inventoryItem.findMany({
    where: { userId: session.user.id },
    include: { item: true },
    orderBy: { purchasedAt: 'desc' },
  });

  return NextResponse.json({ inventory });
}

const equipSchema = z.object({
  itemId: z.string(),
  equip: z.boolean(),
});

export async function PATCH(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const userId = session.user.id;

  try {
    const body = await req.json();
    const parsed = equipSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid data.' }, { status: 400 });
    }

    const { itemId, equip } = parsed.data;

    // Verify ownership
    const inventoryItem = await prisma.inventoryItem.findUnique({
      where: { userId_itemId: { userId, itemId } },
      include: { item: true },
    });

    if (!inventoryItem) {
      return NextResponse.json({ error: 'Item not in inventory.' }, { status: 404 });
    }

    await prisma.$transaction(async (tx) => {
      // If equipping, unequip others in same category
      if (equip) {
        await tx.inventoryItem.updateMany({
          where: {
            userId,
            equipped: true,
            item: { category: inventoryItem.item.category },
          },
          data: { equipped: false },
        });
      }

      // Update this item
      await tx.inventoryItem.update({
        where: { userId_itemId: { userId, itemId } },
        data: { equipped: equip },
      });

      // Update character equipped slots
      const character = await tx.character.findUnique({ where: { userId } });
      if (character && equip) {
        const updateData: Record<string, string | null> = {};
        if (inventoryItem.item.category === 'FRAME') updateData.equippedFrameId = itemId;
        if (inventoryItem.item.category === 'AURA') updateData.equippedAuraId = itemId;
        if (inventoryItem.item.category === 'BADGE') updateData.equippedBadgeId = itemId;
        if (Object.keys(updateData).length > 0) {
          await tx.character.update({ where: { userId }, data: updateData });
        }
      } else if (character && !equip) {
        const updateData: Record<string, null> = {};
        if (inventoryItem.item.category === 'FRAME') updateData.equippedFrameId = null;
        if (inventoryItem.item.category === 'AURA') updateData.equippedAuraId = null;
        if (inventoryItem.item.category === 'BADGE') updateData.equippedBadgeId = null;
        if (Object.keys(updateData).length > 0) {
          await tx.character.update({ where: { userId }, data: updateData });
        }
      }

      // Activity event
      await tx.activityEvent.create({
        data: {
          userId,
          type: 'ITEM_EQUIPPED',
          metadata: JSON.stringify({
            itemId,
            itemName: inventoryItem.item.name,
            action: equip ? 'EQUIPPED' : 'UNEQUIPPED',
          }),
        },
      });
    });

    return NextResponse.json({ success: true, equipped: equip });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to update equipment.' }, { status: 500 });
  }
}
