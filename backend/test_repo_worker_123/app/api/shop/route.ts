// LIFE//OS — Shop Purchase API

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

const purchaseSchema = z.object({
  itemId: z.string().min(1),
});

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const userId = session.user.id;

  try {
    const body = await req.json();
    const parsed = purchaseSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: 'Invalid purchase data.' }, { status: 400 });
    }

    const { itemId } = parsed.data;

    // Load item
    const item = await prisma.item.findUnique({ where: { id: itemId } });
    if (!item) {
      return NextResponse.json({ error: 'Item not found.' }, { status: 404 });
    }

    // Check already owned
    const existing = await prisma.inventoryItem.findUnique({
      where: { userId_itemId: { userId, itemId } },
    });
    if (existing) {
      return NextResponse.json({ error: 'You already own this item.' }, { status: 409 });
    }

    // Check gold
    const character = await prisma.character.findUnique({ where: { userId } });
    if (!character) {
      return NextResponse.json({ error: 'Character not found.' }, { status: 404 });
    }

    if (character.gold < item.price) {
      return NextResponse.json(
        { error: `Not enough Gold. You need ${item.price - character.gold} more Gold.` },
        { status: 402 }
      );
    }

    // Atomic purchase
    const result = await prisma.$transaction(async (tx) => {
      // Deduct gold
      const updatedCharacter = await tx.character.update({
        where: { userId },
        data: { gold: character.gold - item.price },
      });

      // Create inventory record
      const inventoryItem = await tx.inventoryItem.create({
        data: { userId, itemId },
        include: { item: true },
      });

      // Activity event
      await tx.activityEvent.create({
        data: {
          userId,
          type: 'ITEM_PURCHASED',
          metadata: JSON.stringify({
            itemId: item.id,
            itemName: item.name,
            price: item.price,
            goldRemaining: updatedCharacter.gold,
          }),
        },
      });

      return { updatedCharacter, inventoryItem };
    });

    return NextResponse.json({
      success: true,
      item: result.inventoryItem.item,
      goldRemaining: result.updatedCharacter.gold,
    });
  } catch (error) {
    console.error('[PURCHASE ERROR]', error);
    return NextResponse.json({ error: 'Purchase failed. Your Gold is safe.' }, { status: 500 });
  }
}

// GET all shop items
export async function GET(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const [items, ownedItems, character] = await Promise.all([
    prisma.item.findMany({ orderBy: [{ rarity: 'asc' }, { price: 'asc' }] }),
    prisma.inventoryItem.findMany({
      where: { userId: session.user.id },
      select: { itemId: true },
    }),
    prisma.character.findUnique({
      where: { userId: session.user.id },
      select: { gold: true },
    }),
  ]);

  const ownedSet = new Set(ownedItems.map((i) => i.itemId));

  return NextResponse.json({
    items: items.map((item) => ({
      ...item,
      owned: ownedSet.has(item.id),
    })),
    gold: character?.gold ?? 0,
  });
}
