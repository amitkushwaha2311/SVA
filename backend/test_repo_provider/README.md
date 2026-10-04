# LIFE//OS — RPG Life Progression System

Turn your real-world activities into an RPG progression system. Complete real-life quests, build habits, gain XP and Gold, level up, battle personal bosses, unlock behavioral traits, purchase cosmetics, and evolve your character over time.

---

## ⚡ Tech Stack & Architecture

- **Framework**: Next.js 16 (App Router) + React 19 + TypeScript
- **Styling & Animations**: Vanilla CSS Design Tokens + Framer Motion
- **Database & ORM**: PostgreSQL + Prisma ORM
- **Authentication**: NextAuth.js (Credentials Provider with bcrypt password hashing)
- **State & Game Engine**: Server-authoritative RPG Engine with Atomic Prisma Transactions

---

## 🚀 Getting Started

### 1. Environment Setup

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Configure your PostgreSQL connection string in `.env.local`:

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/lifeos?schema=public"
NEXTAUTH_SECRET="your-super-secret-key"
NEXTAUTH_URL="http://localhost:3000"
```

### 2. Database Migration & Seed

Run Prisma migrations and seed default shop items & traits:

```bash
npx prisma db push
npx tsx prisma/seed.ts
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in Chrome to launch **LIFE//OS**.

---

## 🎮 Core RPG Features

- **Character Attributes**: INTELLECT, STRENGTH, DISCIPLINE, CREATIVITY, SOCIAL, RECOVERY
- **Quests & Multi-Completions**: Daily & recurring quest execution history
- **Habits Tracking**: Daily and weekly habit building with streaks and attribute XP rewards
- **Boss Battles**: Deal attribute damage to bosses like *Procrastination Overlord* by completing quests
- **Emergent Behavioral Traits**: Unlock traits like *Deep Worker*, *Relentless*, or *Night Owl* automatically based on your activity patterns
- **Shop & Inventory**: Equip cosmetic avatar frames, auras, and badges using earned Gold
- **Server Authoritative Security**: All XP, Gold, Level-ups, and Streaks are computed server-side in atomic database transactions
