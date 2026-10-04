// LIFE//OS — Signup API Route

import { NextRequest, NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import { z } from 'zod';
import { prisma } from '@/lib/prisma';
import { ARCHETYPES } from '@/lib/constants';
import { requiredXPForLevel } from '@/lib/constants';

const signupSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
  password: z.string().min(6).max(100),
  archetype: z.string().optional(),
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const parsed = signupSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Invalid signup data', details: parsed.error.flatten() },
        { status: 400 }
      );
    }

    const { name, email, password, archetype = 'THE_BUILDER' } = parsed.data;

    // Check existing user
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
      return NextResponse.json(
        { error: 'An account with this email already exists.' },
        { status: 409 }
      );
    }

    // Hash password
    const passwordHash = await bcrypt.hash(password, 12);

    // Find archetype config
    const archetypeConfig = ARCHETYPES.find((a) => a.id === archetype) ?? ARCHETYPES[0];

    // Create user + character atomically
    const user = await prisma.$transaction(async (tx) => {
      const newUser = await tx.user.create({
        data: {
          name,
          email,
          passwordHash,
        },
      });

      const bonusMap = archetypeConfig.bonusAttributes as Record<string, number>;
      await tx.character.create({
        data: {
          userId: newUser.id,
          archetype: archetypeConfig.name,
          level: 1,
          xp: 0,
          xpToNextLevel: requiredXPForLevel(1),
          gold: 0,
          intellect: 10 + (bonusMap.INTELLECT ?? 0),
          strength: 10 + (bonusMap.STRENGTH ?? 0),
          discipline: 10 + (bonusMap.DISCIPLINE ?? 0),
          creativity: 10 + (bonusMap.CREATIVITY ?? 0),
          social: 10 + (bonusMap.SOCIAL ?? 0),
          recovery: 10 + (bonusMap.RECOVERY ?? 0),
        },
      });

      // Create welcome activity event
      await tx.activityEvent.create({
        data: {
          userId: newUser.id,
          type: 'QUEST_COMPLETED',
          metadata: JSON.stringify({ event: 'WELCOME', archetype: archetypeConfig.name }),
        },
      });

      return newUser;
    });

    return NextResponse.json(
      { message: 'Account created successfully', userId: user.id },
      { status: 201 }
    );
  } catch (error) {
    console.error('[SIGNUP ERROR]', error);
    return NextResponse.json(
      { error: 'Failed to create account. Please try again.' },
      { status: 500 }
    );
  }
}
