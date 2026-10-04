// LIFE//OS — Seed Data
// Seeds items, traits, and abilities into the database

/* eslint-disable @typescript-eslint/no-explicit-any */
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const items = [
  { name: 'CYBER FRAME', description: 'A sleek cyberpunk-inspired profile frame with neon edge lighting.', category: 'FRAME', price: 800, rarity: 'RARE', icon: '🔷' },
  { name: 'FOCUS AURA', description: "An ambient aura that pulses when you're in deep work mode.", category: 'AURA', price: 1200, rarity: 'EPIC', icon: '⚡' },
  { name: 'NEON PROFILE', description: 'A full neon profile effect with customizable color waves.', category: 'EFFECT', price: 1500, rarity: 'EPIC', icon: '🌊' },
  { name: 'LEGENDARY FRAME', description: 'The most prestigious frame. Awarded to those who persist.', category: 'FRAME', price: 3000, rarity: 'LEGENDARY', icon: '👑' },
  { name: 'GHOST BADGE', description: 'For those who operate in silence. A minimalist ghost badge.', category: 'BADGE', price: 600, rarity: 'COMMON', icon: '👻' },
  { name: 'TITAN BADGE', description: 'Awarded to those with exceptional strength stats.', category: 'BADGE', price: 900, rarity: 'RARE', icon: '⚔️' },
  { name: 'SCHOLAR FRAME', description: 'An elegant frame with subtle book-page texture.', category: 'FRAME', price: 700, rarity: 'RARE', icon: '📚' },
  { name: 'SHADOW AURA', description: 'A mysterious dark aura that follows your cursor.', category: 'AURA', price: 2000, rarity: 'LEGENDARY', icon: '🌑' },
  { name: 'XP BURST', description: 'XP orbs burst outward on every quest completion.', category: 'EFFECT', price: 1800, rarity: 'EPIC', icon: '✨' },
  { name: 'EMBER FRAME', description: 'A warm, ember-lit frame for the relentless.', category: 'FRAME', price: 1100, rarity: 'EPIC', icon: '🔥' },
];

const traits = [
  { name: 'DEEP WORKER', description: 'Long-form focus has become part of your pattern. You enter flow states with ease.', icon: '⚡', rarity: 'RARE', conditionKey: 'deep_worker' },
  { name: 'RELENTLESS', description: 'Consistency detected across 30+ days. Nothing stops your momentum.', icon: '🔥', rarity: 'EPIC', conditionKey: 'relentless' },
  { name: 'ATHLETE', description: 'Physical training has become a core part of who you are.', icon: '💪', rarity: 'RARE', conditionKey: 'athlete' },
  { name: 'CREATOR', description: "You build things that didn't exist before. Creativity is your mode.", icon: '🎨', rarity: 'RARE', conditionKey: 'creator' },
  { name: 'GENERALIST', description: 'You grow in all dimensions. No single weakness defines you.', icon: '🌐', rarity: 'EPIC', conditionKey: 'generalist' },
  { name: 'FAST LEARNER', description: 'You reached Level 10 faster than most. Information sticks.', icon: '🧠', rarity: 'RARE', conditionKey: 'fast_learner' },
  { name: 'BALANCED', description: 'You develop all aspects of your character in harmony.', icon: '⚖️', rarity: 'COMMON', conditionKey: 'balanced' },
  { name: 'BUILDER', description: "You don't just start projects. You finish them.", icon: '🔨', rarity: 'RARE', conditionKey: 'builder' },
  { name: 'NIGHT OWL', description: 'Your best work happens when the world is asleep.', icon: '🦉', rarity: 'COMMON', conditionKey: 'night_owl' },
  { name: 'EARLY RISER', description: 'You win the morning. The day is yours before it starts.', icon: '🌅', rarity: 'COMMON', conditionKey: 'early_riser' },
  { name: 'SOCIAL BUTTERFLY', description: 'Connections come naturally to you. People are your power.', icon: '🦋', rarity: 'RARE', conditionKey: 'social_butterfly' },
];

const abilities = [
  { name: 'FOCUS MODE', description: 'Enter a deep focus state. Quest XP +10% for 24h.', requiredLevel: 3, icon: '🎯' },
  { name: 'IRON WILL', description: 'Streaks cannot be broken by missing one day.', requiredLevel: 5, icon: '🛡️' },
  { name: 'DOUBLE DOWN', description: 'Complete two quests in one day for 1.25x XP bonus.', requiredLevel: 7, icon: '⚡' },
  { name: 'ARCHITECT', description: 'Campaign quests grant +20% bonus XP.', requiredLevel: 10, icon: '🏗️' },
  { name: 'BOSS SLAYER', description: 'Boss damage increased by 25%.', requiredLevel: 12, icon: '⚔️' },
  { name: 'SCHOLAR', description: 'INTELLECT quests grant +15% XP.', requiredLevel: 15, icon: '📚' },
  { name: 'TITAN', description: 'STRENGTH quests grant +15% XP.', requiredLevel: 15, icon: '💪' },
  { name: 'ARTISAN', description: 'CREATIVITY quests grant +15% XP.', requiredLevel: 15, icon: '🎨' },
  { name: 'LEGEND', description: 'All rewards permanently increased by 10%.', requiredLevel: 20, icon: '👑' },
  { name: 'TRANSCENDENT', description: 'Combo multiplier cap raised to 2.0x.', requiredLevel: 25, icon: '🌟' },
];

async function main() {
  console.log('🌱 Seeding LIFE//OS database...');

  for (const item of items) {
    await (prisma.item as any).upsert({
      where: { name: item.name },
      update: {},
      create: item,
    });
  }
  console.log(`✅ Seeded ${items.length} items`);

  for (const trait of traits) {
    await (prisma.trait as any).upsert({
      where: { name: trait.name },
      update: {},
      create: trait,
    });
  }
  console.log(`✅ Seeded ${traits.length} traits`);

  for (const ability of abilities) {
    await (prisma.ability as any).upsert({
      where: { name: ability.name },
      update: {},
      create: ability,
    });
  }
  console.log(`✅ Seeded ${abilities.length} abilities`);

  console.log('✅ LIFE//OS database seeded successfully');
}

main()
  .catch((e) => {
    console.error('❌ Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
